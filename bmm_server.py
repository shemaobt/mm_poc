#!/usr/bin/env python3
"""
BMM Server - Biblical Meaning Maps Local Server
================================================
Serves BHSA passage data on demand for the BMM application.

Setup:
    pip install flask text-fabric flask-cors

Usage:
    python bmm_server.py
    
    Then open: http://localhost:5000

Options:
    --port PORT         Port to run on (default: 5000)
    --bhsa-path PATH    Path to local BHSA data (optional, will download if not provided)

Author: Generated for Tripod Ontology v5.2 project
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path

# Check dependencies
try:
    from flask import Flask, jsonify, request, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("=" * 60)
    print("ERROR: Missing dependencies!")
    print("Please run: pip install flask flask-cors text-fabric")
    print("=" * 60)
    sys.exit(1)

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# Global variable for Text-Fabric API
TF_API = None
BHSA_LOADED = False

# ============================================================
# BOOK NAME MAPPINGS
# ============================================================
BOOK_NAMES = {
    "genesis": "Genesis", "gen": "Genesis",
    "exodus": "Exodus", "exod": "Exodus", "ex": "Exodus",
    "leviticus": "Leviticus", "lev": "Leviticus",
    "numbers": "Numbers", "num": "Numbers",
    "deuteronomy": "Deuteronomy", "deut": "Deuteronomy",
    "joshua": "Joshua", "josh": "Joshua",
    "judges": "Judges", "judg": "Judges",
    "ruth": "Ruth",
    "1 samuel": "1_Samuel", "1samuel": "1_Samuel", "1sam": "1_Samuel", "1 sam": "1_Samuel",
    "2 samuel": "2_Samuel", "2samuel": "2_Samuel", "2sam": "2_Samuel", "2 sam": "2_Samuel",
    "1 kings": "1_Kings", "1kings": "1_Kings", "1kgs": "1_Kings", "1 kgs": "1_Kings",
    "2 kings": "2_Kings", "2kings": "2_Kings", "2kgs": "2_Kings", "2 kgs": "2_Kings",
    "isaiah": "Isaiah", "isa": "Isaiah",
    "jeremiah": "Jeremiah", "jer": "Jeremiah",
    "ezekiel": "Ezekiel", "ezek": "Ezekiel",
    "hosea": "Hosea", "hos": "Hosea",
    "joel": "Joel",
    "amos": "Amos",
    "obadiah": "Obadiah", "obad": "Obadiah",
    "jonah": "Jonah",
    "micah": "Micah", "mic": "Micah",
    "nahum": "Nahum", "nah": "Nahum",
    "habakkuk": "Habakkuk", "hab": "Habakkuk",
    "zephaniah": "Zephaniah", "zeph": "Zephaniah",
    "haggai": "Haggai", "hag": "Haggai",
    "zechariah": "Zechariah", "zech": "Zechariah",
    "malachi": "Malachi", "mal": "Malachi",
    "psalms": "Psalms", "psalm": "Psalms", "ps": "Psalms",
    "job": "Job",
    "proverbs": "Proverbs", "prov": "Proverbs",
    "ecclesiastes": "Ecclesiastes", "eccl": "Ecclesiastes", "qoh": "Ecclesiastes",
    "song of songs": "Song_of_songs", "song": "Song_of_songs", "cant": "Song_of_songs", "sos": "Song_of_songs",
    "lamentations": "Lamentations", "lam": "Lamentations",
    "esther": "Esther", "esth": "Esther",
    "daniel": "Daniel", "dan": "Daniel",
    "ezra": "Ezra",
    "nehemiah": "Nehemiah", "neh": "Nehemiah",
    "1 chronicles": "1_Chronicles", "1chronicles": "1_Chronicles", "1chr": "1_Chronicles", "1 chr": "1_Chronicles",
    "2 chronicles": "2_Chronicles", "2chronicles": "2_Chronicles", "2chr": "2_Chronicles", "2 chr": "2_Chronicles",
}


def normalize_book_name(book):
    """Normalize book name to BHSA format."""
    key = book.lower().strip()
    return BOOK_NAMES.get(key, book)


def parse_reference(ref_string):
    """
    Parse a biblical reference string.
    
    Examples:
        "Ruth 1:1-6" -> ("Ruth", 1, 1, 6)
        "Gen 1:1-5" -> ("Genesis", 1, 1, 5)
        "Psalm 23:1-6" -> ("Psalms", 23, 1, 6)
    """
    ref_string = ref_string.strip()
    
    # Pattern: Book Chapter:StartVerse-EndVerse
    pattern = r'^(.+?)\s+(\d+):(\d+)-(\d+)$'
    match = re.match(pattern, ref_string)
    
    if match:
        book = normalize_book_name(match.group(1))
        chapter = int(match.group(2))
        start_verse = int(match.group(3))
        end_verse = int(match.group(4))
        return book, chapter, start_verse, end_verse
    
    # Single verse: Book Chapter:Verse
    pattern2 = r'^(.+?)\s+(\d+):(\d+)$'
    match2 = re.match(pattern2, ref_string)
    
    if match2:
        book = normalize_book_name(match2.group(1))
        chapter = int(match2.group(2))
        verse = int(match2.group(3))
        return book, chapter, verse, verse
    
    # Whole chapter: Book Chapter
    pattern3 = r'^(.+?)\s+(\d+)$'
    match3 = re.match(pattern3, ref_string)
    
    if match3:
        book = normalize_book_name(match3.group(1))
        chapter = int(match3.group(2))
        return book, chapter, 1, 999  # Will be clamped to actual verse count
    
    raise ValueError(f"Could not parse reference: {ref_string}")


def is_mainline(clause_type):
    """Determine if a clause type is mainline (foreground)."""
    mainline_types = {"Way0", "WayX"}
    return clause_type in mainline_types


def get_chain_position(clause_type, prev_type):
    """Determine chain position based on clause type and context."""
    if clause_type in ("Way0", "WayX"):
        if prev_type not in ("Way0", "WayX"):
            return "initial"
        else:
            return "continuation"
    elif prev_type in ("Way0", "WayX") and clause_type not in ("Way0", "WayX"):
        return "break"
    else:
        return "continuation"


def strip_hebrew_grammar(text):
    """
    Strip grammatical elements from Hebrew text to get bare concept.
    Removes articles, prepositions, and other grammatical markers.
    """
    if not text:
        return text
    
    text = text.strip()
    
    # Hebrew definite article patterns (ה with various vowels as prefix)
    # These are the most common prefixed elements
    prefixes_to_strip = [
        'הַ', 'הָ', 'הֶ', 'הְ', 'הּ',  # Definite article variants
        'וְהַ', 'וְהָ', 'וְ',  # Conjunction + article
        'בְּ', 'בַּ', 'בָּ', 'בְ',  # Preposition "in"
        'לְ', 'לַ', 'לָ',  # Preposition "to"
        'מִ', 'מֵ', 'מְ',  # Preposition "from"
        'כְּ', 'כַּ', 'כָּ',  # Preposition "like"
    ]
    
    for prefix in prefixes_to_strip:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    
    return text.strip()


def extract_phrase_lemmas(phrase_node, F, L):
    """
    Extract lemmas of main content words from a phrase.
    Returns a clean, grammar-free representation.
    """
    lemmas = []
    
    for w in L.d(phrase_node, otype="word"):
        pos = F.sp.v(w)
        
        # Skip articles, prepositions, conjunctions
        if pos in ('art', 'prep', 'conj'):
            continue
        
        # Get lemma (dictionary form)
        if hasattr(F, 'lex_utf8'):
            lemma = F.lex_utf8.v(w)
        elif hasattr(F, 'g_lex_utf8'):
            lemma = F.g_lex_utf8.v(w)
        else:
            lemma = F.lex.v(w)
        
        if lemma:
            # Clean up lemma markers
            lemma = lemma.rstrip('/=[]')
            lemmas.append(lemma)
    
    return ' '.join(lemmas) if lemmas else None


def extract_passage(book, chapter, start_verse, end_verse):
    """Extract clause data for a passage from BHSA."""
    global TF_API
    
    if not TF_API:
        raise RuntimeError("BHSA not loaded")
    
    A = TF_API
    F = A.api.F
    L = A.api.L
    T = A.api.T
    
    clauses_data = []
    clause_id = 1
    prev_clause_type = None
    actual_end_verse = start_verse
    
    for verse_num in range(start_verse, end_verse + 1):
        # Get verse node
        try:
            verse_node = T.nodeFromSection((book, chapter, verse_num))
        except Exception:
            verse_node = None
        
        if not verse_node:
            # Might have hit end of chapter
            if verse_num == start_verse:
                raise ValueError(f"Could not find {book} {chapter}:{verse_num}")
            break
        
        actual_end_verse = verse_num
        
        # Get clauses in this verse
        clause_nodes = L.d(verse_node, otype="clause")
        
        for clause_node in clause_nodes:
            # Get clause text (Hebrew)
            clause_text = T.text(clause_node)
            
            # Get clause type
            clause_type = F.typ.v(clause_node) or "Unknown"
            
            # Get words and build gloss
            word_nodes = L.d(clause_node, otype="word")
            glosses = []
            for w in word_nodes:
                gloss = F.gloss.v(w) if hasattr(F, 'gloss') and F.gloss.v(w) else ""
                if gloss:
                    glosses.append(gloss)
            gloss_text = " ".join(glosses)
            
            # Get verb information
            verb_lemma = None
            verb_lemma_ascii = None
            verb_stem = None
            verb_tense = None
            
            for w in word_nodes:
                pos = F.sp.v(w)
                if pos == "verb":
                    # Get Hebrew lemma (for display and mapping)
                    if hasattr(F, 'lex_utf8'):
                        verb_lemma = F.lex_utf8.v(w)
                    elif hasattr(F, 'g_lex_utf8'):
                        verb_lemma = F.g_lex_utf8.v(w)
                    else:
                        verb_lemma = F.lex.v(w)
                    
                    # Also get ASCII version for fallback
                    verb_lemma_ascii = F.lex.v(w)
                    verb_stem = F.vs.v(w)
                    verb_tense = F.vt.v(w)
                    break
            
            # Get subjects, objects, and names
            subjects = []
            objects = []
            names = []
            
            phrase_nodes = L.d(clause_node, otype="phrase")
            for phrase_node in phrase_nodes:
                phrase_function = F.function.v(phrase_node)
                
                # Extract clean lemma-based representation
                clean_phrase = extract_phrase_lemmas(phrase_node, F, L)
                
                if phrase_function == "Subj" and clean_phrase:
                    subjects.append(clean_phrase)
                elif phrase_function == "Objc" and clean_phrase:
                    objects.append(clean_phrase)
                
                # Check for proper names
                for w in L.d(phrase_node, otype="word"):
                    if F.sp.v(w) == "nmpr":
                        # Get lemma form of proper name
                        if hasattr(F, 'lex_utf8'):
                            name = F.lex_utf8.v(w)
                        else:
                            name = F.lex.v(w)
                        if name:
                            names.append(name.rstrip("/=[]"))
            
            # Check for כי
            has_ki = any(F.lex.v(w) == "KJ/" for w in word_nodes)
            
            # Chain position
            chain_pos = get_chain_position(clause_type, prev_clause_type)
            
            # Build clause object
            clause_obj = {
                "clause_id": clause_id,
                "verse": verse_num,
                "text": clause_text.strip(),
                "gloss": gloss_text,
                "clause_type": clause_type,
                "is_mainline": is_mainline(clause_type),
                "chain_position": chain_pos,
                "lemma": verb_lemma.rstrip("/=[]") if verb_lemma else None,
                "lemma_ascii": verb_lemma_ascii.rstrip("/=[]") if verb_lemma_ascii else None,
                "binyan": verb_stem,
                "tense": verb_tense,
                "subjects": subjects,
                "objects": objects,
                "preps": [],
                "has_ki": has_ki,
            }
            
            if names:
                clause_obj["names"] = list(set(names))  # Deduplicate
            
            clauses_data.append(clause_obj)
            clause_id += 1
            prev_clause_type = clause_type
    
    # Build reference string with actual range
    if start_verse == actual_end_verse:
        ref_string = f"{book} {chapter}:{start_verse}"
    else:
        ref_string = f"{book} {chapter}:{start_verse}-{actual_end_verse}"
    
    return {
        "reference": ref_string,
        "source_lang": "hbo",
        "clauses": clauses_data,
        "peak_event": None,
        "spine": ""
    }


# ============================================================
# FLASK ROUTES
# ============================================================

@app.route('/')
def index():
    """Serve the main HTML app."""
    return send_from_directory('.', 'bmm_v5_2_unified.html')


@app.route('/api/status')
def status():
    """Check if server and BHSA are ready."""
    return jsonify({
        "status": "ok" if BHSA_LOADED else "loading",
        "bhsa_loaded": BHSA_LOADED
    })


@app.route('/api/passage')
def get_passage():
    """
    Extract a passage from BHSA.
    
    Query params:
        ref: Biblical reference (e.g., "Ruth 1:1-6")
    """
    ref = request.args.get('ref', '').strip()
    
    if not ref:
        return jsonify({"error": "Missing 'ref' parameter"}), 400
    
    if not BHSA_LOADED:
        return jsonify({"error": "BHSA is still loading. Please wait."}), 503
    
    try:
        book, chapter, start_verse, end_verse = parse_reference(ref)
        passage_data = extract_passage(book, chapter, start_verse, end_verse)
        return jsonify(passage_data)
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Extraction error: {str(e)}"}), 500


@app.route('/api/books')
def list_books():
    """List available books."""
    books = [
        "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
        "Joshua", "Judges", "Ruth", "1_Samuel", "2_Samuel",
        "1_Kings", "2_Kings", "Isaiah", "Jeremiah", "Ezekiel",
        "Hosea", "Joel", "Amos", "Obadiah", "Jonah",
        "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
        "Zechariah", "Malachi", "Psalms", "Job", "Proverbs",
        "Ruth", "Song_of_songs", "Ecclesiastes", "Lamentations",
        "Esther", "Daniel", "Ezra", "Nehemiah",
        "1_Chronicles", "2_Chronicles"
    ]
    return jsonify({"books": books})


# ============================================================
# STARTUP
# ============================================================

def load_bhsa(bhsa_path=None):
    """Load BHSA data using Text-Fabric."""
    global TF_API, BHSA_LOADED
    
    print("=" * 60)
    print("Loading BHSA data...")
    print("=" * 60)
    
    # Determine the path to use
    script_dir = Path(__file__).parent.resolve()
    local_bhsa_data_dir = script_dir / "text-fabric-data"
    local_bhsa_app = local_bhsa_data_dir / "github" / "ETCBC" / "bhsa" / "app"
    local_bhsa_tf = local_bhsa_data_dir / "github" / "ETCBC" / "bhsa" / "tf"

    # Set TF_DATA environment variable so text-fabric knows where to look
    # Text-fabric expects data in ~/text-fabric-data/ or TF_DATA/github/org/repo/
    if local_bhsa_data_dir.exists():
        os.environ['TF_DATA'] = str(local_bhsa_data_dir)

    try:
        from tf.app import use
    except ImportError:
        print("ERROR: text-fabric not installed!")
        print("Run: poetry install")
        sys.exit(1)
    
    try:
        if bhsa_path:
            # User specified a path
            print(f"Loading from specified path: {bhsa_path}")
            TF_API = use(bhsa_path, silent=True)
        elif local_bhsa_app.exists() and local_bhsa_tf.exists():
            # Local data found - use it!
            print(f"Found local BHSA data at: {local_bhsa_app.parent}")
            print("Using local data (no download needed)")
            
            # Try to load directly with Fabric to avoid online checks/dependency downloads
            # caused by the 'bhsa' app wrapper
            version_path = local_bhsa_tf / "2021"
            if version_path.exists():
                print(f"Loading directly via Fabric from: {version_path}")
                from tf.fabric import Fabric
                
                # Auto-discover all available features in the directory to ensure F object has attributes
                # This matches the behavior of the app which usually defines a set of features
                # Filter out hidden files or directories that match glob (like .tf directory if matched or .DS_Store)
                features = [f.stem for f in version_path.glob("*.tf") if not f.name.startswith('.')]
                feature_str = " ".join(features)
                
                # Load all features from the specific version directory
                TF = Fabric(locations=[str(version_path)], silent=True)
                api = TF.load(feature_str)
                
                # Wrap api to match the expected structure (TF_API.api.F is used in code)
                class AppWrapper:
                    def __init__(self, api):
                        self.api = api
                
                TF_API = AppWrapper(api)
                BHSA_LOADED = True
            else:
                # Fallback to use() if 2021 version not found (unlikely if 'tf' exists)
                os.environ['TF_DATA'] = str(local_bhsa_data_dir)
                TF_API = use("ETCBC/bhsa", silent=True, check=False)

        else:
            # Try to download from GitHub
            print("Local BHSA data not found. Attempting to download...")
            print("NOTE: Download can take several minutes and requires:")
            print("  - Stable internet connection")
            print("  - GitHub API access (may hit rate limits)")
            
            github_token = os.environ.get('GITHUB_TOKEN')
            if github_token:
                print(f"  - GitHub token detected (will use for authentication)")
            else:
                print("  - To increase rate limits, set GITHUB_TOKEN environment variable")
                print("    See: https://annotation.github.io/text-fabric/tf/advanced/repo.html#github")
            print()
            # Use silent=True instead of silent='deep' to avoid RateLimitOverview issues
            TF_API = use("ETCBC/bhsa", silent=True)
        
        # Verify that TF_API was actually loaded
        if TF_API is None:
            raise RuntimeError("Text-Fabric API failed to load (returned None)")
        
        # Check if the API is actually functional
        if not hasattr(TF_API, 'api') or TF_API.api is None:
            raise RuntimeError("Text-Fabric API loaded but is not functional")
        
        # Try a simple operation to verify it's working
        try:
            # Just check if we can access the API structure
            if not hasattr(TF_API.api, 'F'):
                raise RuntimeError("Text-Fabric API structure incomplete")
        except Exception as e:
            raise RuntimeError(f"Text-Fabric API verification failed: {e}")
        
        BHSA_LOADED = True
        print("=" * 60)
        print("BHSA loaded successfully!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        print("\nTroubleshooting:")
        print("1. The download can take 10-30 minutes depending on connection speed")
        print("2. Set GITHUB_TOKEN environment variable to increase rate limits:")
        print("   export GITHUB_TOKEN=your_github_token")
        print("   Get a token at: https://github.com/settings/tokens")
        print("3. Or download manually and use --bhsa-path option")
        print("4. Or wait and try again later (rate limits reset hourly)")
        sys.exit(1)
    except Exception as e:
        import traceback
        error_msg = str(e).lower()
        print(f"\nERROR loading BHSA: {e}")
        
        # Check for common issues
        if "rate" in error_msg or "limit" in error_msg:
            print("\n" + "=" * 60)
            print("GITHUB RATE LIMIT ISSUE DETECTED")
            print("=" * 60)
            print("\nTo fix this, set a GitHub token:")
            print("  export GITHUB_TOKEN=your_github_personal_access_token")
            print("\nGet a token at: https://github.com/settings/tokens")
            print("(No special permissions needed, just a token)")
            print("\nThen run the server again:")
            print("  poetry run python bmm_server.py")
            print("\nAlternatively:")
            print("  - Wait an hour for rate limits to reset")
            print("  - Use --bhsa-path to point to already-downloaded data")
        else:
            print("\nFull error traceback:")
            traceback.print_exc()
            print("\nTroubleshooting tips:")
            print("1. Make sure you have internet connection (first time download)")
            print("2. Try specifying a local path with --bhsa-path")
            print("3. Set GITHUB_TOKEN environment variable to avoid rate limits")
            print("4. Update text-fabric: poetry update text-fabric")
        
        sys.exit(1)


def get_local_ip():
    """Get local IP address for network access."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port."""
    import socket
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None


def main():
    parser = argparse.ArgumentParser(description="BMM Server - Serve BHSA passages")
    parser.add_argument("--port", "-p", type=int, default=5000, help="Port (default: 5000)")
    parser.add_argument("--bhsa-path", help="Path to local BHSA text-fabric data")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    
    args = parser.parse_args()
    
    # Load BHSA first
    load_bhsa(args.bhsa_path)
    
    # Check if port is available, try to find alternative if not
    requested_port = args.port
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', requested_port))
    except OSError:
        print(f"WARNING: Port {requested_port} is already in use.")
        if requested_port == 5000:
            print("On macOS, port 5000 is often used by AirPlay Receiver.")
            print("You can disable it in System Settings > General > AirDrop & Handoff")
        print(f"Trying to find an available port...")
        available_port = find_available_port(requested_port + 1)
        if available_port:
            print(f"Using port {available_port} instead.")
            args.port = available_port
        else:
            print(f"ERROR: Could not find an available port. Please specify a different port with --port")
            sys.exit(1)
    
    # Get local IP for display
    local_ip = get_local_ip()
    
    print()
    print("=" * 60)
    print("BMM SERVER READY")
    print("=" * 60)
    print()
    print("Share this URL with workshop participants:")
    print()
    print(f"    http://{local_ip}:{args.port}")
    print()
    print("Or use localhost for your own browser:")
    print()
    print(f"    http://localhost:{args.port}")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    # Run Flask
    app.run(host=args.host, port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()

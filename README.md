# BMM Server - Biblical Meaning Maps Local Server

A Flask-based web server that serves Biblical Hebrew Scripture (BHSA) passage data on demand for the Biblical Meaning Maps (BMM) application. This server provides access to the ETCBC BHSA dataset through a simple web interface and REST API.

## Features

- 🚀 **Easy Setup** - Simple installation with Poetry
- 📖 **BHSA Integration** - Direct access to ETCBC Biblical Hebrew data
- 🌐 **Web Interface** - Built-in HTML interface for passage analysis
- 🔌 **REST API** - JSON API for programmatic access
- 💾 **Local Data Support** - Automatically detects and uses local BHSA data
- 🔒 **Workshop Ready** - Designed for local network workshops

## Prerequisites

- **Python 3.8+** (Python 3.9+ recommended)
- **Poetry** (for dependency management)
- **~500MB disk space** (for BHSA data, if downloading)
- **Internet connection** (for first-time data download, optional if using local data)

## Installation

### 1. Install Poetry

If you don't have Poetry installed:

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Or follow the official guide: https://python-poetry.org/docs/#installation
```

### 2. Clone the Repository

```bash
git clone https://github.com/shemaobt/mm_poc.git
cd mm_poc
```

### 3. Install Dependencies

```bash
poetry install
```

This will install all required dependencies including:
- Flask (web framework)
- Flask-CORS (cross-origin support)
- Text-Fabric (BHSA data access)

## Running the Application

### Basic Usage

```bash
poetry run python bmm_server.py
```

The server will:
1. Check for local BHSA data in `text-fabric-data/github/ETCBC/bhsa/`
2. Use local data if found, or download from GitHub if not
3. Start the Flask server on `http://localhost:5000`

### Command Line Options

```bash
# Specify a custom port
poetry run python bmm_server.py --port 8080

# Use a custom BHSA data path
poetry run python bmm_server.py --bhsa-path /path/to/bhsa/app

# Specify host (default: 0.0.0.0 for network access)
poetry run python bmm_server.py --host 127.0.0.1

# Combine options
poetry run python bmm_server.py --port 8080 --bhsa-path ~/bhsa-data/app
```

### First-Time Setup

On first run, if no local BHSA data is found, the server will attempt to download it from GitHub. This can take 10-30 minutes depending on your connection.

**To speed up the download**, set a GitHub token:

```bash
export GITHUB_TOKEN=your_github_personal_access_token
poetry run python bmm_server.py
```

Get a token at: https://github.com/settings/tokens (no special permissions needed)

## Accessing the Application

Once the server is running, you'll see output like:

```
============================================================
BMM SERVER READY
============================================================

Share this URL with workshop participants:

    http://192.168.1.100:5000

Or use localhost for your own browser:

    http://localhost:5000
```

- **Local access**: Open `http://localhost:5000` in your browser
- **Network access**: Use the IP address shown (e.g., `http://192.168.1.100:5000`)

## API Endpoints

### GET `/`
Serves the main HTML application interface.

### GET `/api/status`
Check server and BHSA loading status.

**Response:**
```json
{
  "status": "ok",
  "bhsa_loaded": true
}
```

### GET `/api/passage?ref=PASSAGE_REFERENCE`
Extract passage data from BHSA.

**Parameters:**
- `ref` (required): Biblical reference (e.g., "Ruth 1:1-6", "Gen 1:1-5", "Psalm 23:1-6")

**Response:**
```json
{
  "reference": "Ruth 1:1-6",
  "source_lang": "hbo",
  "clauses": [
    {
      "clause_id": 1,
      "verse": 1,
      "text": "וַיְהִי בִּימֵי שְׁפֹט הַשֹּׁפְטִים",
      "gloss": "And it came to pass in the days when the judges judged",
      "clause_type": "Way0",
      "is_mainline": true,
      "chain_position": "initial",
      "lemma": "היה",
      "subjects": ["ימים"],
      "objects": [],
      ...
    }
  ]
}
```

### GET `/api/books`
List all available books in the BHSA dataset.

**Response:**
```json
{
  "books": ["Genesis", "Exodus", "Leviticus", ...]
}
```

## Local Data Setup

The server automatically detects BHSA data in the following location:

```
text-fabric-data/github/ETCBC/bhsa/
├── app/
│   ├── app.py
│   └── config.yaml
└── tf/
    └── 2021/
        └── *.tf files
```

If you have BHSA data elsewhere, you can:

1. **Symlink it** to the expected location:
   ```bash
   ln -s /path/to/your/bhsa-data text-fabric-data/github/ETCBC/bhsa
   ```

2. **Use `--bhsa-path`** to point directly to the app directory:
   ```bash
   poetry run python bmm_server.py --bhsa-path /path/to/bhsa/app
   ```

3. **Set `TF_DATA` environment variable**:
   ```bash
   export TF_DATA=/path/to/text-fabric-data
   poetry run python bmm_server.py
   ```

## Development

### Project Structure

```
mm_poc/
├── bmm_server.py          # Main Flask server
├── bmm_v5_2_unified.html  # Web application interface
├── generate_assets.py      # Asset generation script
├── pyproject.toml         # Poetry dependencies
├── .gitignore            # Git ignore rules
└── text-fabric-data/     # BHSA data (gitignored)
```

### Running in Development Mode

For development, you might want to enable Flask's debug mode. Edit `bmm_server.py` and change:

```python
app.run(host=args.host, port=args.port, debug=True, threaded=True)
```

Or add a `--debug` flag to the argument parser.

### Dependencies

Key dependencies are managed via Poetry:
- **Flask 3.0+** - Web framework
- **Flask-CORS 4.0+** - Cross-origin resource sharing
- **Text-Fabric** - BHSA data access library
- **PyGithub <2.0.0** - GitHub API (for data download)

## Troubleshooting

### Port Already in Use

If port 5000 is already in use (common on macOS with AirPlay):

```bash
# Use a different port
poetry run python bmm_server.py --port 8080

# Or disable AirPlay Receiver in System Settings > General > AirDrop & Handoff
```

### BHSA Loading Fails

**Rate Limit Errors:**
```bash
# Set GitHub token
export GITHUB_TOKEN=your_token
poetry run python bmm_server.py
```

**Data Not Found:**
- Ensure `text-fabric-data/github/ETCBC/bhsa/` exists with proper structure
- Or use `--bhsa-path` to specify location
- Check that both `app/` and `tf/` directories exist

**Connection Issues:**
- Verify internet connection (for first-time download)
- Check firewall settings
- Ensure sufficient disk space (~500MB)

### Server Not Accessible on Network

- Ensure server is bound to `0.0.0.0` (default)
- Check firewall allows incoming connections on the port
- Verify all devices are on the same network
- Try accessing via `localhost` first to verify server is running

### Text-Fabric Errors

If you encounter `RateLimitOverview` or similar errors:

1. Ensure PyGithub version is compatible:
   ```bash
   poetry show pygithub
   ```

2. Update dependencies:
   ```bash
   poetry update
   ```

## Requirements

- **Python**: 3.8 or higher (3.9+ recommended)
- **Disk Space**: ~500MB for BHSA data
- **Memory**: Minimum 2GB RAM recommended
- **Network**: Required only for first-time data download

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please open an issue on GitHub: https://github.com/shemaobt/mm_poc

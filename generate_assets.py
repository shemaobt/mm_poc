import json
import os
import time
from elevenlabs.client import ElevenLabs
from elevenlabs import save

# ================= CONFIGURATION =================
# 1. PASTE YOUR KEYS INSIDE THE QUOTES BELOW
API_KEY = ceb562ae54e9e423a978ba74c27786057d915169283bcfa17059a40d7278db45
VOICE_ID = wmiJT1Zvn57mFFHkEXsq 

OUTPUT_FOLDER = "workshop_assets"
AUDIO_FOLDER = os.path.join(OUTPUT_FOLDER, "audio")

# 2. YOUR ATI-UNA DATA (I have paired your text with the English translations)
raw_segments = [
    ("Nya ka boro li na korsae tamba we, a tomu nyana li soro kamba.", "The hunter heard that a lion was nearby, so he became very afraid."),
    ("A tara we so, nya ka siri li mo tembo ya.", "He hid behind a big tree and waited quietly."),
    ("Korsae we bora, a nya li kamba moro we.", "The lion passed by, not seeing the man hiding."),
    ("A kele we: 'Tamba li soro kamba! Nya moro we bora!'", "He said: 'The lion is very close! The man has escaped!'"),
    ("Mansa we tara li mo kele ya.", "The chief did not want to listen."),
    ("Nya we bora mo fero kono, a segi ka so.", "The man went into the forest, and then came back."),
    ("Tomu we kele: 'A bora ka soro!'", "The elder said: 'He has gone far away!'"),
    ("A teri we segi li mo tanba ya kono.", "His friend returned to the village."),
    ("Bora we nya li mo fero ya.", "Everyone in the village was happy."),
    ("Kele we: 'Ala we kamba nya li!'", "The people said: 'God has protected our brother!'")
]
# =================================================

client = ElevenLabs(api_key=API_KEY)

def setup_folders():
    if not os.path.exists(AUDIO_FOLDER):
        os.makedirs(AUDIO_FOLDER)
    print(f"📂 Created folders in '{OUTPUT_FOLDER}/'")

def generate_workshop_data():
    setup_folders()
    final_segments = []
    
    print(f"🚀 Starting generation for {len(raw_segments)} segments...")
    print("------------------------------------------------------")

    for i, (transcript, translation) in enumerate(raw_segments):
        filename = f"segment_{i}.mp3"
        filepath = os.path.join(AUDIO_FOLDER, filename)
        
        # 1. Generate Audio (skips if file already exists)
        if not os.path.exists(filepath):
            print(f"🔊 Generating audio for segment {i}...")
            try:
                audio = client.text_to_speech.convert(
                    text=transcript,
                    voice_id=VOICE_ID,
                    model_id="eleven_multilingual_v2"
                )
                save(audio, filepath)
                time.sleep(0.5) # Pause to be kind to the API
            except Exception as e:
                print(f"❌ Error generating segment {i}: {e}")
                # We continue so one error doesn't stop the whole batch
        else:
            print(f"⏭️  Audio for segment {i} already exists. Skipping.")

        # 2. Create Data Object
        segment_data = {
            "id": i,
            "transcript": transcript,
            "translation": translation,
            "audio_file": f"audio/{filename}",
            "duration": 5, 
            # Default AI suggestions for the pilot
            "aiSuggestions": {
                "is_speaking": {"value": "no", "confidence": 0.8},
                "is_moving": {"value": "no", "confidence": 0.8},
                "event_subtype": {"value": "ACTION", "confidence": 0.7},
                "evidentiality": {"value": "witnessed_visual", "confidence": 0.6},
                "reality": {"value": "actual", "confidence": 0.9},
                "time_frame": {"value": "immediate", "confidence": 0.8},
                "discourse_function": {"value": "MAIN", "confidence": 0.7},
                "affect": {"value": "neutral", "confidence": 0.6},
                "open_ended": {"value": "no_additional", "confidence": 0.9}
            }
        }
        final_segments.append(segment_data)

    # 3. Save as a JS file
    js_content = f"const WORKSHOP_DATA = {json.dumps(final_segments, indent=4)};"
    with open(os.path.join(OUTPUT_FOLDER, "data.js"), "w", encoding="utf-8") as f:
        f.write(js_content)
    
    print("------------------------------------------------------")
    print(f"✅ DONE! All assets saved to '{OUTPUT_FOLDER}'")
    print(f"📝 data.js created.")

if __name__ == "__main__":
    generate_workshop_data()
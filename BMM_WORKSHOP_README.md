# BMM Workshop Server Setup

## Quick Start

### 1. Install Poetry (if needed)

```bash
# Install Poetry: https://python-poetry.org/docs/#installation
# Or on macOS: curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Install Dependencies (One Time)

**Using Poetry (Recommended):**

```bash
poetry install
```

**Or using pip (Alternative):**

```bash
pip install flask flask-cors text-fabric
```

### 2. (Optional) Set GitHub Token for Faster Downloads

If you encounter rate limit errors during the first download, set a GitHub token:

```bash
export GITHUB_TOKEN=your_github_personal_access_token
```

Get a token at: https://github.com/settings/tokens (no special permissions needed)

### 3. Start the Server

**Using Poetry:**

```bash
poetry run python bmm_server.py
```

**Or using pip:**

```bash
python bmm_server.py
```

**Local Data Detection:** The server automatically detects and uses local BHSA data if it exists in `text-fabric-data/github/ETCBC/bhsa/`. If not found, it will attempt to download from GitHub.

**First time (if no local data):** BHSA will download (~300MB). This can take 10-30 minutes depending on:
- Your internet connection speed
- GitHub API rate limits (use GITHUB_TOKEN to avoid this)
- Network stability

**With local data or after download:** Server starts in seconds.

### 3. Share the URL

The server will display something like:

```
Share this URL with workshop participants:

    http://192.168.1.100:5000
```

Give this URL to your participants. They open it in any browser.

---

## What Participants See

1. Text box to type any passage (e.g., "Ruth 1:1-6")
2. Click "Fetch Passage" — data loads from BHSA
3. Click "Pre-fill All Fields with AI" — Claude analyzes the passage
4. Review and validate all stages
5. Export JSON

---

## Options

### Use Local BHSA Data

**Automatic Detection:** The server automatically looks for local BHSA data in `text-fabric-data/github/ETCBC/bhsa/` relative to the script location. If found, it will use it automatically.

**Manual Path:** If your data is in a different location:

```bash
# With Poetry
poetry run python bmm_server.py --bhsa-path /path/to/bhsa/app

# Or with pip
python bmm_server.py --bhsa-path /path/to/bhsa/app
```

Note: Point to the `app` directory within the BHSA data structure.

### Change Port

```bash
# With Poetry
poetry run python bmm_server.py --port 8080

# Or with pip
python bmm_server.py --port 8080
```

---

## Troubleshooting

### "Server not detected" in browser

- Make sure server is running
- Make sure you're on the same WiFi network
- Try http://localhost:5000 on your own machine first

### Participants can't connect

- Check firewall settings on your laptop
- Make sure everyone is on the same network
- Try creating a mobile hotspot from your laptop

### BHSA loading fails or rate limit errors

**Rate Limit Issues:**
- Set `GITHUB_TOKEN` environment variable (see step 2 above)
- Or wait an hour for rate limits to reset
- Or use `--bhsa-path` to point to already-downloaded data

**Other Issues:**
- Check internet connection (first time needs to download)
- First download can take 10-30 minutes - be patient
- Try specifying local path with `--bhsa-path` if you have the data already
- Make sure you have enough disk space (~500MB)

---

## File Overview

| File | Purpose |
|------|---------|
| `bmm_server.py` | Flask server, serves BHSA passages |
| `bmm_v5_2_unified.html` | The web app (served by bmm_server.py) |
| `etcbc_to_bmm.py` | Standalone script for offline JSON export |

---

## Workshop Flow

1. **Before workshop**: Run server once to download BHSA
2. **Workshop day**: Start server, share URL
3. **During workshop**: Participants request any passage on demand
4. **You**: Can work on other things, just keep terminal open

---

## Requirements

- Python 3.8+
- ~500MB disk space for BHSA data
- WiFi network (all participants must be on same network)
- Modern web browser (Chrome, Firefox, Safari, Edge)

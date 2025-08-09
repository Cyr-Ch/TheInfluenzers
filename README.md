# TheInfluenzers

Automates generating short-form video scripts with OpenAI, fetching stock footage from Pexels, formatting to vertical with FFmpeg, and uploading to YouTube.

## Requirements
- Python 3.9+
- FFmpeg installed and available in PATH

## Setup
1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your keys:
   ```env
   OPENAI_API_KEY=sk-...
   PEXELS_API_KEY=pxl-...
   # Optional: path to your Google OAuth client secrets JSON
   CLIENT_SECRET_FILE=client_secret.json
   ```
4. Place your Google OAuth client file at the path specified by `CLIENT_SECRET_FILE`.

## Usage
Run the main script and follow the prompt:
```bash
python main.py
```

## Notes
- `.env` is loaded automatically by `config.py` via python-dotenv.
- Sensitive files like `.env` and `client_secret.json` are ignored by git via `.gitignore`.

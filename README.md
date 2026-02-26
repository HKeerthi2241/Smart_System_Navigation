# Voice LLM (LM Studio + Mistral + Whisper + gTTS)

### Steps to Run

1. Start LM Studio locally with `Mistral 7B` model (make sure API is available at `http://localhost:1234`).
2. Install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

3. Install FFmpeg (add to PATH, verify with `ffmpeg -version`).
4. Run the project:

```bash
python main.py
```

You can ask about either **gitam_shivaji_bhavan** or **guild_cafe** — the model will give randomized 30–60s spoken outputs.

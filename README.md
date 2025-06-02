# 🎙 Speechify TTS Streamlit App

This is a simple Streamlit app that lets you convert text into audio using Speechify's TTS API.

## ✅ Features
- Enter your Speechify API Key
- Fetch and select available voices
- Customize:
  - Emotion (13 styles)
  - Pitch (-50% to +50%)
  - Speed (-50% to +50%)
  - Volume (x-soft to x-loud)
- Play and download the result as MP3

## 🚀 Usage

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 📁 Project Structure

- `app.py` – Main UI
- `utils/speechify_api.py` – API interaction logic
- `output/` – Folder to save audio
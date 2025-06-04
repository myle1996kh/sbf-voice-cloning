# 🎙️ SBF Voice Cloning

> *"Your voice reflects your thoughts. Change your voice, and you may just change your mind."*

Have you ever felt like your voice isn’t truly *you*?

Maybe it’s too soft. Too fast. Lacking confidence. Flat in emotion.  
But what if you could **design your ideal voice** – a voice that feels confident, expressive, and uniquely yours?

**SBF (Sound-Based Foundation)** is a tool to help you explore that possibility.

### 🌟 What is SBF Voice Cloning?

SBF Voice Cloning allows you to:
- Input any text
- Customize how it sounds: **emotion**, **pitch**, **speed**, **volume**
- And generate an audio file using your desired voice style – powered by Speechify’s ultra-realistic voice API.

You can:
- Create podcast episodes in the *version of your voice you dream of*
- Practice public speaking by listening to *how you want to sound*
- Let it **soak into your subconscious** – the more you hear it, the more you become it.

### 🎯 Why?

Because voice is more than sound.  
It’s identity. Energy. Expression.  
And sometimes, all it takes to become a better version of yourself... is to hear it first.

Let SBF Voice Cloning be the version of your voice you wish to become.

---

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

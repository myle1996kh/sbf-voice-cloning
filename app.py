import streamlit as st
from utils.speechify_api import fetch_voice_ids, generate_audio_with_params, EMOTION_OPTIONS

st.set_page_config(page_title="SBF - Chunks - TTS App", layout="centered")
st.title("🎧 SBF - CHUNKS - Voice Generator")

api_key = st.text_input("🔑 Enter your API Key", type="password")

if api_key:
    voice_options = fetch_voice_ids(api_key)
    if voice_options:
        voice_names = [f"{v[0]} ({v[1][:8]}...)" for v in voice_options]
        voice_map = {f"{v[0]} ({v[1][:8]}...)": v[1] for v in voice_options}

        selected_voice_name = st.selectbox("🎤 Select a Voice", voice_names)
        selected_voice_id = voice_map[selected_voice_name]

        st.code(f"Selected Voice ID: {selected_voice_id}", language="bash")

        text_input = st.text_area("📝 Enter Text to Synthesize")

        col1, col2 = st.columns(2)
        with col1:
            emotion = st.selectbox("🎭 Emotion", EMOTION_OPTIONS, index=8)  # default: assertive
            volume = st.selectbox("🔊 Volume", ["x-soft", "soft", "medium", "loud", "x-loud"], index=2)
        with col2:
            pitch = st.slider("🎚 Pitch %", -50, 50, 0)
            rate = st.slider("🚀 Speed %", -50, 100, 0)

        if st.button("🚀 Generate Audio") and text_input.strip():
            with st.spinner("Generating audio..."):
                output_file = generate_audio_with_params(
                    api_key, selected_voice_id, text_input,
                    emotion, pitch, rate, volume
                )

            if output_file:
                audio_bytes = open(output_file, 'rb').read()
                st.audio(audio_bytes, format='audio/mp3')
                st.download_button("⬇️ Download MP3", audio_bytes, file_name="output.mp3")
            else:
                st.error("Failed to generate audio. Check your API key or text input.")
    else:
        st.warning("⚠️ Could not fetch voices. You may manually input a Voice ID below.")
        custom_voice_id = st.text_input("Or paste a Voice ID manually")
        text_input = st.text_area("📝 Enter Text to Synthesize")

        col1, col2 = st.columns(2)
        with col1:
            emotion = st.selectbox("🎭 Emotion", EMOTION_OPTIONS, index=8)
            volume = st.selectbox("🔊 Volume", ["x-soft", "soft", "medium", "loud", "x-loud"], index=2)
        with col2:
            pitch = st.slider("🎚 Pitch %", -50, 50, 0)
            rate = st.slider("🚀 Speed %", -50, 100, 0)

        if st.button("🚀 Generate Audio") and text_input.strip() and custom_voice_id.strip():
            with st.spinner("Generating audio..."):
                output_file = generate_audio_with_params(
                    api_key, custom_voice_id.strip(), text_input,
                    emotion, pitch, rate, volume
                )

            if output_file:
                audio_bytes = open(output_file, 'rb').read()
                st.audio(audio_bytes, format='audio/mp3')
                st.download_button("⬇️ Download MP3", audio_bytes, file_name="output.mp3")
            else:
                st.error("Failed to generate audio. Please check your Voice ID or API Key.")
                st.error("Failed to generate audio. Check your API key or text input.")
        st.warning("⚠️ Could not fetch voices. Check your API key.")
else:
    st.info("👆 Please enter your API key to begin.")
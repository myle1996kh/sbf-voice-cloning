import streamlit as st
from utils.speechify_api import generate_audio_with_params, EMOTION_OPTIONS, generate_demo_audio
from utils.voice_utils import init_voice_db, get_voice_id, save_voice_to_db, load_all_voice_ids
from utils.yt_utils import get_youtube_transcript, extract_video_id
from utils.transcript_db import init_transcript_db, save_transcript, load_all_transcripts, get_transcript_by_id
import os

from io import BytesIO

# ----------------------------
# ✅ Setup
# ----------------------------
st.set_page_config(page_title="Chunks Voice Editor", layout="wide")
st.title("🎧 Chunks Voice Editor")

API_KEY = "W1vp8RVy2tnAw0GEj0NPqRszlWIXCfiDyLR5qOsY1rw="
init_voice_db()
init_transcript_db()

# ----------------------------
# 📌 Sidebar Navigation
# ----------------------------
st.sidebar.image("assests/logo.png", width=180)
st.sidebar.markdown("<h2 style='text-align:left; font-size: 22px;'>🧭 SOUND-BASED FOUNDATION</h2>", unsafe_allow_html=True)
tabs = st.sidebar.radio(
    "Navigation",  # Provide a non-empty label for accessibility
    ["Voice Setup", "Transcript", "Generate Audio", "Manage Files"],
    label_visibility="collapsed",
    key="main_tabs",
    # Custom style for radio buttons
)
# Custom CSS for radio button font size
st.markdown(
    """
    <style>
    div[data-testid="stSidebar"] div[role="radiogroup"] label {
        font-size: 15px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# 🧱 Tab 1: Upload / Record / Select Voice
# ----------------------------
if tabs == "Voice Setup":
    st.header("🔊 Upload, Record or Select a Voice")

    voice_mode = st.radio(
        "Choose voice source", 
        ["Use Existing Voice ID", "Upload New Voice (MP3)", "Record Your Voice"], 
        horizontal=True
    )

    global selected_voice_id
    selected_voice_id = None

    if voice_mode == "Use Existing Voice ID":
        voice_entries = load_all_voice_ids()
        if voice_entries:
            name_to_id = {f"{name} ({vid[:8]})": vid for name, vid in voice_entries}
            selected_name = st.selectbox("Select a saved voice", list(name_to_id.keys()))
            selected_voice_id = name_to_id[selected_name]
            st.success(f"✅ Selected Voice ID: {selected_voice_id}")
        else:
            st.warning("⚠️ No saved voice IDs found. Please upload or record a new voice.")

    elif voice_mode == "Upload New Voice (MP3)":
        name = st.text_input("Name your voice")
        audio_file = st.file_uploader("Upload your voice (MP3)", type=["mp3"])
        if st.button("Upload & Create Voice") and name and audio_file:
            audio_path = os.path.join("output", f"{name}.mp3")
            with open(audio_path, "wb") as f:
                f.write(audio_file.read())
            with st.spinner("Creating voice..."):
                voice_id = get_voice_id(name, audio_path)
            if voice_id:
                save_voice_to_db(name, voice_id, audio_path)
                selected_voice_id = voice_id
                st.success(f"✅ Created and saved Voice ID: {voice_id}")
            else:
                st.error("❌ Failed to create voice.")

    elif voice_mode == "Record Your Voice":
        from st_audiorec import st_audiorec

        name = st.text_input("Name your recorded voice")
        # Thêm chọn transcript từ history để đọc khi record
        transcripts = load_all_transcripts()
        transcript_text = ""
        if transcripts:
            transcript_choices = {f"{row[1]} ({row[2]})": row[0] for row in transcripts}
            selected_label = st.selectbox("Select transcript to read while recording", list(transcript_choices.keys()))
            selected_id = transcript_choices[selected_label]
            transcript_text = get_transcript_by_id(selected_id)
            st.markdown("**Transcript to read:**")
            st.text_area("Transcript for recording", transcript_text, height=180)
        else:
            st.info("No transcripts found. Please add a transcript in the 'Transcript' tab.")

        st.subheader("🎙 Record below and click 'Create Voice' after:")
        wav_audio_data = st_audiorec()

        if wav_audio_data is not None:
            st.audio(wav_audio_data, format='audio/wav')
            temp_audio_path = os.path.join("output", "recorded_voice.wav")
            with open(temp_audio_path, "wb") as f:
                f.write(wav_audio_data)

            if st.button("🎯 Create Voice from Recording") and name:
                with st.spinner("Creating voice from recording..."):
                    voice_id = get_voice_id(name, temp_audio_path)
                if voice_id:
                    save_voice_to_db(name, voice_id, temp_audio_path)
                    selected_voice_id = voice_id
                    st.success(f"✅ Created and saved Voice ID: {voice_id}")
                else:
                    st.error("❌ Failed to create voice from recording.")

# ----------------------------
# 🧱 Block 2: Select or Load Transcript
# ----------------------------
if tabs == "Transcript":
    st.header("📚Transcript from YouTube")

    from utils.yt_utils import get_youtube_transcript, extract_video_id
    from utils.transcript_db import (
        init_transcript_db, save_transcript,
        load_all_transcripts, get_transcript_by_id
    )

    init_transcript_db()

    tab_mode = st.radio("📥 Transcript Source", ["Paste YouTube Link", "Load from History"], horizontal=True)
    transcript = ""
    video_id = ""

    if tab_mode == "Paste YouTube Link":
        yt_url = st.text_input("Paste YouTube video link")

        if st.button("📄 Fetch Transcript"):
            with st.spinner("Getting transcript..."):
                video_id = extract_video_id(yt_url)
                transcript_text, video_title = get_youtube_transcript(yt_url)

            if transcript_text:
                st.session_state["transcript"] = transcript_text
                save_transcript(source=video_title, video_id=video_id, transcript=transcript_text)
                st.success("✅ Transcript fetched and saved.")
            else:
                st.error("❌ Could not fetch transcript.")

    elif tab_mode == "Load from History":
        transcripts = load_all_transcripts()
        if transcripts:
            choices = {f"{row[1]} ({row[2]})": row[0] for row in transcripts}
            selected_label = st.selectbox("Select a saved transcript", list(choices.keys()))
            selected_id = choices[selected_label]
            transcript = get_transcript_by_id(selected_id)
            st.session_state["transcript"] = transcript
        else:
            st.warning("⚠️ No saved transcripts found.")

    # 🧾 Show transcript & char count
    transcript = st.session_state.get("transcript", "")
    if transcript:
        st.markdown(f"📏 Characters: `{len(transcript)}`")
        st.text_area("📜 Transcript", value=transcript, height=300)

# ----------------------------
# 🧱 Tab 3: Generate Audio
# ----------------------------
elif tabs == "Generate Audio":
    st.header("🎛 Customize & Generate Audio")

    input_mode = st.radio("Transcript Source", ["Select from history", "Input custom text"], horizontal=True)
    transcript = ""
    if input_mode == "Select from history":
        transcripts = load_all_transcripts()
        if not transcripts:
            st.warning("⚠️ No transcripts found. Please go to 'Transcript' tab to fetch.")
            transcript = ""
        else:
            transcript_choices = {f"{row[1]} ({row[2]})": row[0] for row in transcripts}
            selected_label = st.selectbox("Select transcript from history", list(transcript_choices.keys()))
            selected_id = transcript_choices[selected_label]
            original_transcript = get_transcript_by_id(selected_id)
            transcript = st.text_area("Transcript Preview (you can edit before generating audio)", value=original_transcript, height=200)
    else:
        transcript = st.text_area("Enter your custom transcript here", value="", height=200)

    st.session_state["transcript"] = transcript

    voice_entries = load_all_voice_ids()
    if not voice_entries:
        st.warning("⚠️ No saved voice IDs found. Go to 'Voice Setup' tab.")
    else:
        name_to_id = {f"{name} ({vid[:8]})": vid for name, vid in voice_entries}
        selected_name = st.selectbox("Select a voice for synthesis", list(name_to_id.keys()))
        selected_voice_id = name_to_id[selected_name]

        col1, col2 = st.columns(2)
        with col1:
            emotion = st.selectbox("🎭 Emotion", EMOTION_OPTIONS, index=13)
            volume = st.selectbox("🔊 Volume", ["x-soft", "soft", "medium", "loud", "x-loud"], index=2)
        with col2:
            pitch = st.slider("🎚 Pitch %", -50, 50, 0)
            rate = st.slider("🚀 Speed %", -100, 100, 0)

        # Demo Button
        if st.button("🧪 Demo / Preview (max 200 chars)"):
            with st.spinner("Generating demo audio..."):
                from utils.speechify_api import generate_demo_audio
                output_file = generate_demo_audio(
                    API_KEY, selected_voice_id, transcript,
                    emotion, pitch, rate, volume,
                    output_path=None
                )
            if output_file:
                audio_bytes = open(output_file, "rb").read()
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button("⬇️ Download Demo", audio_bytes, file_name=os.path.basename(output_file))
            else:
                st.error("❌ Failed to generate demo audio.")

        if st.button("🚀 Generate Full Audio"):
            with st.spinner("Generating full audio..."):
                output_file = generate_audio_with_params(
                    API_KEY, selected_voice_id, transcript,
                    emotion, pitch, rate, volume
                )
            if output_file:
                audio_bytes = open(output_file, "rb").read()
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button("⬇️ Download Full", audio_bytes, file_name=os.path.basename(output_file))
            else:
                st.error("❌ Failed to generate full audio.")

# ----------------------------
# 🧱 Tab 4: Manage Files
# ----------------------------
import glob
if tabs == "Manage Files":
    st.header("📁 Manage Output Files")
    output_files = glob.glob(os.path.join("output", "*"))
    output_files = [f for f in output_files if os.path.isfile(f)]
    if not output_files:
        st.info("No files found in the output folder.")
    else:
        files_per_row = 3
        for i in range(0, len(output_files), files_per_row):
            cols = st.columns(files_per_row)
            for idx, file_path in enumerate(output_files[i:i+files_per_row]):
                file_name = os.path.basename(file_path)
                with cols[idx]:
                    st.markdown(f"<div style='text-align:left; font-weight:bold; margin-bottom:15px;'>{file_name}</div>", unsafe_allow_html=True)
                    if file_name.lower().endswith(('.mp3', '.wav')):
                        audio_bytes = open(file_path, "rb").read()
                        st.audio(audio_bytes, format="audio/mp3" if file_name.endswith(".mp3") else "audio/wav")
                    # Download & Play buttons are hidden
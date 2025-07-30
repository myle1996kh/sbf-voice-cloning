import streamlit as st
from utils.speechify_api import generate_audio_with_params, EMOTION_OPTIONS, generate_demo_audio
from utils.voice_utils import init_voice_db, get_voice_id, save_voice_to_db, load_all_voice_ids
from utils.yt_utils import get_youtube_transcript, extract_video_id
from utils.transcript_db import init_transcript_db, save_transcript, load_all_transcripts, get_transcript_by_id
from utils.nlp_processor import process_speech_to_text, correct_grammar_with_gintler
from utils.mirror_talk_db import (
    init_mirror_talk_db, save_mirror_talk_session, load_all_mirror_talk_sessions,
    delete_mirror_talk_session, get_mirror_talk_stats
)
from st_audiorec import st_audiorec
import os
import glob
from datetime import datetime
from io import BytesIO

# ----------------------------
# ✅ Setup
# ----------------------------
st.set_page_config(page_title="Chunks - VOICE CLONING", layout="wide")
st.title("🎧 Chunks - VOICE CLONING")

API_KEY = "W1vp8RVy2tnAw0GEj0NPqRszlWIXCfiDyLR5qOsY1rw="

# Initialize directories and databases
os.makedirs("output", exist_ok=True)
init_voice_db()
init_transcript_db()
init_mirror_talk_db()

# ----------------------------
# 📌 Sidebar Navigation
# ----------------------------
st.sidebar.image("assests/logo.png", width=180)
st.sidebar.markdown("<h2 style='text-align:left; font-size: 22px;'>🧭 SOUND-BASED FOUNDATION</h2>", unsafe_allow_html=True)
tabs = st.sidebar.radio(
    "Navigation",
    ["Voice Setup", "Transcript", "Generate Podcast", "Mirror Talk", "Manage Files"],
    label_visibility="collapsed",
    key="main_tabs"
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
        name = st.text_input("Name your recorded voice")
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
# 🧱 Tab 2: Complete Transcript Management with Enhanced YouTube Support
# ----------------------------
elif tabs == "Transcript":  # ✅ FIX: Changed to elif
    st.header("📚 Transcript Management")
    
    # Enhanced radio options with upload functionality
    tab_mode = st.radio(
        "📥 Transcript Source", 
        ["Upload Text File", "Load from History"], 
        horizontal=True
    )
    
    transcript = ""
    video_id = ""
    
    # Option 1: Enhanced YouTube Link with Better Error Handling
   
    # Option 2: Upload Text File  
    if tab_mode == "Upload Text File":
        st.subheader("📁 Upload Transcript File")
        
        uploaded_file = st.file_uploader(
            "Choose a text file",
            type=['txt', 'srt', 'vtt'],
            help="Supported formats: .txt, .srt, .vtt"
        )
        
        if uploaded_file is not None:
            try:
                # Read file content
                if uploaded_file.type == "text/plain":
                    transcript_content = str(uploaded_file.read(), "utf-8")
                else:
                    # Handle subtitle files (.srt, .vtt)
                    content = str(uploaded_file.read(), "utf-8")
                    if uploaded_file.name.endswith('.srt'):
                        # Basic SRT parsing - remove timestamps and indices
                        lines = content.split('\n')
                        transcript_lines = []
                        for line in lines:
                            line = line.strip()
                            # Skip empty lines, numbers, and timestamp lines
                            if (line and 
                                not line.isdigit() and 
                                '-->' not in line and
                                not re.match(r'^\d{2}:\d{2}:\d{2}', line)):
                                transcript_lines.append(line)
                        transcript_content = ' '.join(transcript_lines)
                    elif uploaded_file.name.endswith('.vtt'):
                        # Basic VTT parsing
                        lines = content.split('\n')
                        transcript_lines = []
                        skip_next = False
                        for line in lines:
                            line = line.strip()
                            if line.startswith('WEBVTT') or line.startswith('NOTE'):
                                continue
                            if '-->' in line:
                                skip_next = True
                                continue
                            if skip_next and line == '':
                                skip_next = False
                                continue
                            if line and not skip_next:
                                transcript_lines.append(line)
                        transcript_content = ' '.join(transcript_lines)
                    else:
                        transcript_content = content
                
                if transcript_content.strip():
                    st.session_state["transcript"] = transcript_content
                    
                    # Generate a unique identifier for uploaded files
                    file_id = f"upload_{uploaded_file.name}_{len(transcript_content)}"
                    
                    # Save to database
                    save_transcript(
                        source=f"📁 {uploaded_file.name}",
                        video_id=file_id,
                        transcript=transcript_content
                    )
                    
                    st.success(f"✅ File uploaded and saved: {uploaded_file.name}")
                    st.info(f"📏 Characters loaded: {len(transcript_content):,}")
                    
                    # Show preview
                    with st.expander("👀 Preview Uploaded Content"):
                        preview_text = transcript_content[:300] + "..." if len(transcript_content) > 300 else transcript_content
                        st.text_area("Preview:", value=preview_text, height=100, disabled=True)
                else:
                    st.error("❌ The uploaded file appears to be empty")
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
                st.info("💡 **Tips:**\n"
                       "- Ensure file is properly encoded (UTF-8)\n"
                       "- Check file format (.txt, .srt, .vtt)\n"
                       "- Try saving the file in a different format")
        
        # File format help
        with st.expander("ℹ️ Supported File Formats"):
            st.markdown("""
            **📄 Plain Text (.txt)**
            - Simple text files with transcript content
            - Most common and straightforward format
            
            **🎬 SubRip (.srt)**
            - Subtitle files with timestamps
            - Format: sequence number, timestamp, text
            - Timestamps and numbers will be automatically removed
            
            **🎥 WebVTT (.vtt)**
            - Web Video Text Tracks format
            - Used for HTML5 video subtitles
            - WEBVTT headers and timestamps will be cleaned
            """)
    
    # Option 3: Load from History
    elif tab_mode == "Load from History":
        st.subheader("📚 Saved Transcripts")
        
        transcripts = load_all_transcripts()
        if transcripts:
            # ✅ FIX: Updated to handle the new format with saved_date
            choices = {}
            for row in transcripts:
                # Handle both old format (4 items) and new format (5 items)
                if len(row) == 5:
                    transcript_id, source, video_id, transcript_text, saved_date = row
                else:
                    transcript_id, source, video_id, transcript_text = row
                    saved_date = "Unknown date"
                
                # Format the display string
                if video_id.startswith('upload_'):
                    display_name = f"📁 {source} • {saved_date}"
                else:
                    display_name = f"🎥 {source} • {saved_date}"
                choices[display_name] = transcript_id
            
            # Search functionality
            search_term = st.text_input("🔍 Search transcripts", placeholder="Search by title or content...")
            
            if search_term:
                # Filter choices based on search term
                filtered_choices = {k: v for k, v in choices.items() if search_term.lower() in k.lower()}
                if filtered_choices:
                    choices = filtered_choices
                    st.info(f"Found {len(filtered_choices)} matching transcripts")
                else:
                    st.warning("No transcripts match your search")
                    choices = {}
            
            if choices:
                selected_label = st.selectbox(
                    "Select a saved transcript",
                    list(choices.keys()),
                    help="Choose from your previously saved transcripts"
                )
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    load_btn = st.button("📖 Load Selected", type="primary")
                with col2:
                    if st.button("👀 Preview", type="secondary"):
                        selected_id = choices[selected_label]
                        preview_transcript = get_transcript_by_id(selected_id)
                        if preview_transcript:
                            st.session_state['preview_transcript'] = preview_transcript[:500] + "..." if len(preview_transcript) > 500 else preview_transcript
                with col3:
                    if st.button("🗑️ Delete Selected", type="secondary"):
                        # Add confirmation
                        if st.session_state.get('confirm_delete', False):
                            selected_id = choices[selected_label]
                            # ✅ FIX: Using existing delete_transcript function
                            if delete_transcript(selected_id):
                                st.success("✅ Transcript deleted")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete transcript")
                            st.session_state['confirm_delete'] = False  # Reset confirmation
                        else:
                            st.session_state['confirm_delete'] = True
                            st.warning("⚠️ Click again to confirm deletion")
                
                # Show preview if requested
                if 'preview_transcript' in st.session_state:
                    st.markdown("**📖 Preview:**")
                    st.text_area("", value=st.session_state['preview_transcript'], height=100, disabled=True)
                    if st.button("❌ Close Preview"):
                        del st.session_state['preview_transcript']
                        st.rerun()
                
                if load_btn:
                    selected_id = choices[selected_label]
                    transcript = get_transcript_by_id(selected_id)
                    if transcript:
                        st.session_state["transcript"] = transcript
                        st.success("✅ Transcript loaded successfully")
                        # Clear preview if it exists
                        if 'preview_transcript' in st.session_state:
                            del st.session_state['preview_transcript']
                    else:
                        st.error("❌ Could not load transcript")
        else:
            st.warning("⚠️ No saved transcripts found.")
            st.info("💡 Upload a file or fetch from YouTube to get started!")
    
    # Display current transcript with enhanced UI
    transcript = st.session_state.get("transcript", "")
    if transcript:
        st.markdown("---")
        st.subheader("📜 Current Transcript")
        
        # Stats row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📏 Characters", f"{len(transcript):,}")
        with col2:
            word_count = len(transcript.split())
            st.metric("📝 Words", f"{word_count:,}")
        with col3:
            # Estimate reading time (average 200 words per minute)
            read_time = max(1, word_count // 200)
            st.metric("⏱️ Read Time", f"~{read_time} min")
        with col4:
            # Estimate speaking time (average 150 words per minute)
            speak_time = max(1, word_count // 150)
            st.metric("🎤 Speak Time", f"~{speak_time} min")
        
        # Transcript display with copy functionality
        transcript_display = st.text_area(
            "Transcript Content",
            value=transcript,
            height=300,
            help="Your transcript content is displayed here. You can edit it before generating audio."
        )
        
        # Update session state if transcript was edited
        if transcript_display != transcript:
            st.session_state["transcript"] = transcript_display
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("📋 Copy to Clipboard"):
                st.code(transcript, language=None)
                st.success("📋 Content ready to copy!")
        with col2:
            if st.button("💾 Save Edited"):
                if transcript_display != transcript:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    save_transcript(
                        source=f"✏️ Edited Version {timestamp}",
                        video_id=f"edited_{timestamp}",
                        transcript=transcript_display
                    )
                    st.success("💾 Edited version saved!")
                else:
                    st.info("No changes to save")
        with col3:
            if st.button("🔄 Clear Transcript"):
                st.session_state["transcript"] = ""
                st.rerun()
        with col4:
            # Download as file
            if st.download_button(
                "📥 Download",
                data=transcript,
                file_name=f"transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            ):
                st.success("📥 Transcript downloaded!")
    else:
        st.info("💡 No transcript loaded. Choose an option above to get started!")
# ----------------------------
# 🧱 Tab 3: Generate Podcast
# ----------------------------
elif tabs == "Generate Podcast":
    st.header("🎛 Customize & Generate Podcast")

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
# 🧱 Tab 4: Mirror Talk - NEW FEATURE
# ----------------------------
elif tabs == "Mirror Talk":
    st.header("🪞 Mirror Talk - Record, Improve & Clone")
    st.markdown("*Record your speech, get grammar-corrected version in your cloned voice*")

    # Voice & Audio Settings - Collapsed
    with st.expander("🎤 Voice & Audio Settings", expanded=False):
        # Voice Selection Block
        voice_entries = load_all_voice_ids()
        if not voice_entries:
            st.warning("⚠️ No saved voice IDs found. Go to 'Voice Setup' tab first.")
            st.stop()
        
        name_to_id = {f"{name} ({vid[:8]})": vid for name, vid in voice_entries}
        selected_name = st.selectbox("🎤 Select your cloned voice", list(name_to_id.keys()))
        selected_voice_id = name_to_id[selected_name]
        st.success(f"✅ Using Voice: {selected_voice_id[:12]}...")
        
        st.markdown("---")
        st.subheader("🎛️ Audio Settings")
        col1, col2 = st.columns(2)
        with col1:
            emotion = st.selectbox("🎭 Emotion", EMOTION_OPTIONS, index=7)  # Default to "calm"
            volume = st.selectbox("🔊 Volume", ["x-soft", "soft", "medium", "loud", "x-loud"], index=2)
        with col2:
            pitch = st.slider("🎚 Pitch %", -50, 50, 0)
            rate = st.slider("🚀 Speed %", -100, 100, 0)
    
    # Handle case when expander is collapsed - use default values
    if 'selected_voice_id' not in locals():
        voice_entries = load_all_voice_ids()
        if not voice_entries:
            st.warning("⚠️ No saved voice IDs found. Go to 'Voice Setup' tab first.")
            st.stop()
        name_to_id = {f"{name} ({vid[:8]})": vid for name, vid in voice_entries}
        selected_voice_id = list(name_to_id.values())[0]  # Use first voice as default
        emotion = "calm"
        volume = "medium"
        pitch = 0
        rate = 0

    # Recording Section
    st.subheader("🎙️ Record Your Speech")
    st.info("💡 Tip: Press 'Stop Recording' to automatically save and process your speech!")
    
    wav_audio_data = st_audiorec()

    if wav_audio_data is not None:
        # Show the recorded audio
        st.audio(wav_audio_data, format='audio/wav')
        
        # Auto-trigger processing immediately when recording stops
        # Generate timestamp for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        with st.spinner("🎯 Processing your speech..."):
            # Step 1: Save recorded audio with unique filename
            temp_audio_path = os.path.join("output", f"mirror_original_{timestamp}.wav")
            with open(temp_audio_path, "wb") as f:
                f.write(wav_audio_data)
            
            # Step 2: Convert speech to text
            try:
                original_text = process_speech_to_text(temp_audio_path)
                if not original_text:
                    st.error("❌ Could not extract text from your recording. Please try again.")
                    st.stop()
                
            except Exception as e:
                st.error(f"❌ Speech recognition error: {str(e)}")
                st.stop()

        with st.spinner("🧠 Improving grammar with Gintler AI..."):
            # Step 3: Process through NLP for grammar correction
            try:
                corrected_text = correct_grammar_with_gintler(original_text)
                if not corrected_text:
                    st.warning("⚠️ Grammar correction failed, using original text.")
                    corrected_text = original_text
                
            except Exception as e:
                st.warning(f"⚠️ Grammar correction error: {str(e)}")
                corrected_text = original_text

        with st.spinner("🎵 Generating improved audio with your cloned voice..."):
            # Step 4: Generate audio using corrected text and cloned voice
            try:
                # Create unique filename for generated audio
                generated_audio_path = os.path.join("output", f"mirror_generated_{timestamp}.mp3")
                
                output_file = generate_audio_with_params(
                    API_KEY, selected_voice_id, corrected_text,
                    emotion, pitch, rate, volume,
                    output_path=generated_audio_path
                )
                
                if output_file:
                    # Get voice name for database
                    voice_name = selected_name.split(" (")[0]  # Extract name without ID
                    
                    # Save session to database
                    session_name = f"Mirror Talk {timestamp}"
                    session_id = save_mirror_talk_session(
                        session_name=session_name,
                        voice_id=selected_voice_id,
                        voice_name=voice_name,
                        original_text=original_text,
                        corrected_text=corrected_text,
                        emotion=emotion,
                        pitch=pitch,
                        rate=rate,
                        volume=volume,
                        original_audio_path=temp_audio_path,
                        generated_audio_path=output_file
                    )
                    
                    st.success("🎉 Mirror Talk completed successfully!")
                    
                    # Main Results - Focus on Audio Comparison
                    st.markdown("---")
                    st.subheader("🎭 Audio Comparison")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**🎤 Your Original Recording**")
                        st.audio(wav_audio_data, format='audio/wav')
                    
                    with col2:
                        st.markdown("**✨ Improved Version (Your Cloned Voice)**")
                        audio_bytes = open(output_file, "rb").read()
                        st.audio(audio_bytes, format="audio/mp3")
                        st.download_button(
                            "⬇️ Download Improved Audio", 
                            audio_bytes, 
                            file_name=os.path.basename(output_file),
                            key="download_mirror",
                            use_container_width=True
                        )
                    
                    # Detailed Results in Expander
                    with st.expander("📝 Text Comparison & Processing Details", expanded=False):
                        # Processing Status
                        st.success("✅ Speech-to-text completed!")
                        st.success("✅ Grammar correction completed!")
                        st.success("🎉 Mirror Talk completed successfully!")
                        
                        st.info(f"💾 Session saved as: {session_name} (ID: {session_id})")
                        
                        detail_col1, detail_col2 = st.columns(2)
                        with detail_col1:
                            st.caption("📝 Original Text:")
                            st.text_area("Original", value=original_text, height=100, disabled=True)
                        
                        with detail_col2:
                            st.caption("✨ Corrected Text:")
                            st.text_area("Corrected", value=corrected_text, height=100, disabled=True)
                        
                        # Show improvements if any
                        if original_text != corrected_text:
                            st.success("🔍 **Grammar Improvements Applied!** Compare the texts above to see what was corrected.")
                        else:
                            st.info("👌 **Perfect Grammar!** Your original speech was already grammatically correct.")
                        
                        # Settings Used
                        st.caption("🎛️ Settings Used:")
                        setting_cols = st.columns(4)
                        with setting_cols[0]:
                            st.metric("Emotion", emotion)
                        with setting_cols[1]:
                            st.metric("Volume", volume)
                        with setting_cols[2]:
                            st.metric("Pitch", f"{pitch}%")
                        with setting_cols[3]:
                            st.metric("Speed", f"{rate}%")
                        
                else:
                    st.error("❌ Failed to generate improved audio. Please try again.")
                    # Clean up original file if generation failed
                    try:
                        os.remove(temp_audio_path)
                    except:
                        pass
                    
            except Exception as e:
                st.error(f"❌ Audio generation error: {str(e)}")
                # Clean up files if error occurred
                try:
                    os.remove(temp_audio_path)
                except:
                    pass

    # Tips and Instructions
    with st.expander("💡 How Mirror Talk Works"):
        st.markdown("""
        **Mirror Talk** helps you improve your speech by:
        
        1. **🎙️ Start Recording** - Begin capturing your speech
        2. **🛑 Stop Recording** - Automatically saves and starts processing
        3. **📝 Transcription** - Converts your speech to text using advanced AI
        4. **✨ Grammar Correction** - Fixes grammar and improves clarity with Gintler AI
        5. **🎵 Voice Cloning** - Generates the improved version using your cloned voice
        6. **🔄 Compare** - Listen to both versions side-by-side
        
        **Best Practices:**
        - Speak clearly and at normal pace
        - Use complete sentences
        - Adjust settings in the Audio Settings section if needed
        - Practice regularly to improve your natural speech patterns
        """)
    
    # Recent Sessions
    with st.expander("📋 Recent Mirror Talk Sessions"):
        recent_sessions = load_all_mirror_talk_sessions()[:5]  # Show last 5 sessions
        if recent_sessions:
            for session in recent_sessions:
                session_id, session_name, voice_name, original_text, corrected_text, emotion, pitch, rate, volume, original_audio_path, generated_audio_path, created_at = session
                
                st.markdown(f"**{session_name}** - {voice_name} ({created_at})")
                
                # Audio playback for recent sessions
                if generated_audio_path and os.path.exists(generated_audio_path):
                    session_audio_col1, session_audio_col2 = st.columns(2)
                    
                    with session_audio_col1:
                        st.caption("Original:")
                        if original_audio_path and os.path.exists(original_audio_path):
                            with open(original_audio_path, "rb") as f:
                                st.audio(f.read(), format="audio/wav")
                        else:
                            st.text("Original audio not available")
                    
                    with session_audio_col2:
                        st.caption("Improved:")
                        with open(generated_audio_path, "rb") as f:
                            audio_bytes = f.read()
                            st.audio(audio_bytes, format="audio/mp3")
                
                # Text preview
                text_preview_col1, text_preview_col2 = st.columns(2)
                with text_preview_col1:
                    st.caption("Original Text:")
                    st.text(original_text[:80] + "..." if len(original_text) > 80 else original_text)
                with text_preview_col2:
                    st.caption("Improved Text:")
                    st.text(corrected_text[:80] + "..." if len(corrected_text) > 80 else corrected_text)
                
                st.markdown("---")
        else:
            st.info("No recent sessions found. Start your first Mirror Talk session above!")
# ----------------------------
# 🧱 Tab 5: Improved File Management with Better UI
# ----------------------------
elif tabs == "Manage Files":
    st.header("📁 Manage Output Files")
    
    # Create tabs for different file types
    file_tabs = st.tabs(["🪞 Mirror Talk Sessions", "📂 File Browser"])
    
    # Tab 1: Mirror Talk Sessions (Table View)
    with file_tabs[0]:
        st.subheader("🪞 Mirror Talk Sessions")
        mirror_sessions = load_all_mirror_talk_sessions()
        
        if not mirror_sessions:
            st.info("No Mirror Talk sessions found. Create some in the Mirror Talk tab!")
        else:
            # Summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Sessions", len(mirror_sessions))
            with col2:
                total_size = 0
                for session in mirror_sessions:
                    if session[10] and os.path.exists(session[10]):  # generated_audio_path
                        total_size += os.path.getsize(session[10])
                st.metric("Total Size", f"{total_size / (1024*1024):.1f} MB")
            with col3:
                today_sessions = [s for s in mirror_sessions if s[11].startswith(datetime.now().strftime("%Y-%m-%d"))]
                st.metric("Today's Sessions", len(today_sessions))
            
            st.markdown("---")
            
            # Table view with pagination
            sessions_per_page = 5
            total_pages = (len(mirror_sessions) + sessions_per_page - 1) // sessions_per_page
            
            if total_pages > 1:
                page = st.selectbox("📄 Page", range(1, total_pages + 1), format_func=lambda x: f"Page {x}")
                start_idx = (page - 1) * sessions_per_page
                end_idx = start_idx + sessions_per_page
                sessions_to_show = mirror_sessions[start_idx:end_idx]
            else:
                sessions_to_show = mirror_sessions
            
            for session in sessions_to_show:
                session_id, session_name, voice_name, original_text, corrected_text, emotion, pitch, rate, volume, original_audio_path, generated_audio_path, created_at = session
                
                with st.container():
                    # Session header
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**{session_name}**")
                        st.caption(f"Voice: {voice_name} | {created_at}")
                    with col2:
                        if generated_audio_path and os.path.exists(generated_audio_path):
                            file_size = os.path.getsize(generated_audio_path) / 1024  # KB
                            st.caption(f"📊 {file_size:.1f} KB")
                    with col3:
                        if st.button("🗑️", key=f"del_session_{session_id}", help="Delete session"):
                            if delete_mirror_talk_session(session_id):
                                st.success("Session deleted!")
                                st.rerun()
                    
                    # Expandable details with improved layout
                    with st.expander(f"📝 Details & Audio"):
                        # Upper section: Text comparison
                        details_col1, details_col2 = st.columns(2)
                        
                        with details_col1:
                            st.markdown("**📝 Original Text:**")
                            st.text_area("", value=original_text[:200] + "..." if len(original_text) > 200 else original_text, 
                                       height=80, key=f"orig_text_{session_id}", disabled=True)
                        
                        with details_col2:
                            st.markdown("**✨ Corrected Text:**")
                            st.text_area("", value=corrected_text[:200] + "..." if len(corrected_text) > 200 else corrected_text, 
                                       height=80, key=f"corr_text_{session_id}", disabled=True)
                        
                        # Middle section: Settings
                        st.markdown("**🎛️ Settings:**")
                        settings_info = f"Emotion: {emotion} | Pitch: {pitch}% | Speed: {rate}% | Volume: {volume}"
                        st.caption(settings_info)
                        
                        st.markdown("---")
                        
                        # Bottom section: Audio comparison (Original on left, Generated on right)
                        audio_col1, audio_col2 = st.columns(2)
                        
                        with audio_col1:
                            st.markdown("**🎤 Original Recording:**")
                            if original_audio_path and os.path.exists(original_audio_path):
                                with open(original_audio_path, "rb") as f:
                                    original_audio_bytes = f.read()
                                    st.audio(original_audio_bytes, format="audio/wav")
                                    st.download_button(
                                        "⬇️ Download Original", 
                                        original_audio_bytes, 
                                        file_name=f"original_{os.path.basename(original_audio_path)}",
                                        key=f"download_original_{session_id}"
                                    )
                            else:
                                st.info("Original audio not available")
                        
                        with audio_col2:
                            st.markdown("**🎵 Generated Audio (Your Cloned Voice):**")
                            if generated_audio_path and os.path.exists(generated_audio_path):
                                with open(generated_audio_path, "rb") as f:
                                    generated_audio_bytes = f.read()
                                    st.audio(generated_audio_bytes, format="audio/mp3")
                                    st.download_button(
                                        "⬇️ Download Generated", 
                                        generated_audio_bytes, 
                                        file_name=os.path.basename(generated_audio_path),
                                        key=f"download_generated_{session_id}"
                                    )
                            else:
                                st.error("Generated audio not found")
                
                st.markdown("---")
    
    # Tab 2: File Browser (Card View)
    with file_tabs[1]:
        st.subheader("📂 File Browser")
        
        # File type filter
        file_filter = st.radio(
            "Filter by type:",
            ["🔄 All Files", "🪞 Mirror Talk", "🎵 Generated Audio", "🎤 Voice Records"],
            horizontal=True
        )
        
        output_files = glob.glob(os.path.join("output", "*"))
        output_files = [f for f in output_files if os.path.isfile(f)]
        
        # Apply filter
        if file_filter == "🪞 Mirror Talk":
            filtered_files = [f for f in output_files if "mirror_" in os.path.basename(f)]
        elif file_filter == "🎵 Generated Audio":
            filtered_files = [f for f in output_files if f.endswith('.mp3') and "mirror_" not in os.path.basename(f)]
        elif file_filter == "🎤 Voice Records":
            filtered_files = [f for f in output_files if f.endswith('.wav')]
        else:
            filtered_files = output_files
        
        if not filtered_files:
            st.info("No files found matching the selected filter.")
        else:
            # Sort options
            sort_by = st.selectbox("Sort by:", ["📅 Date (Newest)", "📅 Date (Oldest)", "📊 Size (Largest)", "🔤 Name"])
            
            if sort_by == "📅 Date (Newest)":
                filtered_files.sort(key=os.path.getmtime, reverse=True)
            elif sort_by == "📅 Date (Oldest)":
                filtered_files.sort(key=os.path.getmtime)
            elif sort_by == "📊 Size (Largest)":
                filtered_files.sort(key=os.path.getsize, reverse=True)
            else:  # Name
                filtered_files.sort(key=lambda x: os.path.basename(x))
            
            # Pagination for files
            files_per_page = 9  # 3x3 grid
            total_file_pages = (len(filtered_files) + files_per_page - 1) // files_per_page
            
            if total_file_pages > 1:
                file_page = st.selectbox("📄 Files Page", range(1, total_file_pages + 1), 
                                       format_func=lambda x: f"Page {x} of {total_file_pages}")
                start_file_idx = (file_page - 1) * files_per_page
                end_file_idx = start_file_idx + files_per_page
                files_to_show = filtered_files[start_file_idx:end_file_idx]
            else:
                files_to_show = filtered_files
            
            # Display files in grid
            for i in range(0, len(files_to_show), 3):
                cols = st.columns(3)
                for idx, file_path in enumerate(files_to_show[i:i+3]):
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    file_date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d %H:%M")
                    
                    with cols[idx]:
                        # File card
                        with st.container():
                            # File icon and name
                            if file_name.endswith('.mp3'):
                                icon = "🎵"
                            elif file_name.endswith('.wav'):
                                icon = "🎤"
                            else:
                                icon = "📄"
                            
                            st.markdown(f"**{icon} {file_name[:20]}{'...' if len(file_name) > 20 else ''}**")
                            st.caption(f"📊 {file_size:.1f} KB | 📅 {file_date}")
                            
                            # Audio player for audio files
                            if file_name.lower().endswith(('.mp3', '.wav')):
                                try:
                                    audio_bytes = open(file_path, "rb").read()
                                    st.audio(audio_bytes, format="audio/mp3" if file_name.endswith(".mp3") else "audio/wav")
                                except:
                                    st.error("❌ Cannot play audio")
                            
                            # Action buttons
                            button_col1, button_col2 = st.columns(2)
                            with button_col1:
                                if file_name.lower().endswith(('.mp3', '.wav')):
                                    audio_bytes = open(file_path, "rb").read()
                                    st.download_button("⬇️", audio_bytes, file_name=file_name, 
                                                     key=f"dl_file_{i}_{idx}")
                            with button_col2:
                                if st.button("🗑️", key=f"del_file_{i}_{idx}", help="Delete file"):
                                    try:
                                        os.remove(file_path)
                                        st.success("File deleted!")
                                        st.rerun()
                                    except:
                                        st.error("Failed to delete")
                        
                        st.markdown("---")

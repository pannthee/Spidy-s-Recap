```python
import streamlit as st
import os
import tempfile
import json
import time
import subprocess
import shutil
import math
from pathlib import Path
from datetime import timedelta
import base64

# Third-party libraries (Requires: streamlit, groq, google-genai, edge-tts, pydub, srt)
# Note: assemblyai is required for fallback. moviepy is intentionally avoided due to RAM usage on small instances, using raw ffmpeg.
try:
    from groq import Groq
except ImportError:
    st.error("Missing groq library. Please install: pip install groq")
    st.stop()

try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error("Missing google-genai library. Please install: pip install google-genai")
    st.stop()

try:
    from pydub import AudioSegment
except ImportError:
    st.error("Missing pydub library. Please install: pip install pydub")
    st.stop()
    
try:
    import srt
except ImportError:
    st.error("Missing srt library. Please install: pip install srt")
    st.stop()

# Helper to check for ffmpeg
def check_ffmpeg():
    if not shutil.which("ffmpeg"):
        st.error("ffmpeg is not installed or not in PATH. This app requires ffmpeg to process audio and video.")
        st.stop()

check_ffmpeg()

st.set_page_config(
    page_title="Spidy Dub Studio",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'flow_state' not in st.session_state:
    st.session_state.flow_state = 'init' # init -> transcribed -> translated -> generated -> merged
if 'segments' not in st.session_state:
    st.session_state.segments = []
if 'video_path' not in st.session_state:
    st.session_state.video_path = None
if 'audio_path' not in st.session_state:
    st.session_state.audio_path = None
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if 'api_keys' not in st.session_state:
    st.session_state.api_keys = {'groq': '', 'gemini': '', 'assemblyai': ''}

with st.sidebar:
    st.title("🕷️ Spidy Dub Studio")
    st.markdown("ဗီဒီယိုထဲက စာသားပြောအပိုင်းတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးတဲ့ tool.")
    
    st.header("🔑 API Keys")
    st.markdown("Keys are kept in your session. Set them in Streamlit Secrets for permanent usage.")
    
    # Check secrets first
    groq_secret = st.secrets.get("GROQ_API_KEY", "")
    gemini_secret = st.secrets.get("GEMINI_API_KEY", "")
    aai_secret = st.secrets.get("ASSEMBLYAI_API_KEY", "")

    st.session_state.api_keys['groq'] = st.text_input("Groq API Key (Whisper)", value=groq_secret, type="password")
    st.session_state.api_keys['gemini'] = st.text_input("Gemini API Key (Translation/Recap)", value=gemini_secret, type="password")
    
    st.header("⚙️ Settings")
    use_aai_fallback = st.checkbox("Enable AssemblyAI Fallback (if Groq 403s)", value=True)
    if use_aai_fallback:
        st.session_state.api_keys['assemblyai'] = st.text_input("AssemblyAI API Key", value=aai_secret, type="password")
        
    mode = st.radio("🎬 Mode Selection", ["Standard Dub", "Recap Studio", "Narrator Mode"], 
                    help="Standard: Fits audio to video. Recap: Alters video speed to fit narration. Narrator: Gemini watches and narrates scenes.")
    
    auto_merge = st.checkbox("Auto-merge short segments", value=True, help="Merge short Whisper segments (< 1s) to prevent rushed audio.")
    auto_shorten = st.checkbox("Auto-shorten translations", value=True, help="Ask Gemini to shorten translations if TTS audio exceeds segment time.")
    
    if st.button("Reset Session", type="primary"):
        st.session_state.flow_state = 'init'
        st.session_state.segments = []
        if st.session_state.video_path and os.path.exists(st.session_state.video_path):
            os.remove(st.session_state.video_path)
        st.rerun()

def extract_audio(video_path, output_audio_path):
    """Extract audio using ffmpeg, optimized for Whisper API size limits (16k, mono, 32k bitrate)"""
    command = [
        "ffmpeg", "-y", "-i", video_path,
        "-vn", "-acodec", "libmp3lame",
        "-ac", "1", "-ar", "16000", "-b:a", "32k",
        output_audio_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def merge_short_segments(segments, min_duration=1.5):
    """Merge segments that are too short to give TTS enough breathing room"""
    if not segments:
        return []
    
    merged = []
    current_seg = segments[0]
    
    for next_seg in segments[1:]:
        curr_duration = current_seg['end'] - current_seg['start']
        # If current is too short, or gap between them is very small, merge
        if curr_duration < min_duration or (next_seg['start'] - current_seg['end'] < 0.5):
            current_seg['end'] = next_seg['end']
            current_seg['text'] += " " + next_seg['text']
        else:
            merged.append(current_seg)
            current_seg = next_seg
            
    merged.append(current_seg)
    return merged

def transcribe_groq(audio_path, api_key):
    """Transcribe using Groq API"""
    client = Groq(api_key=api_key)
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), file.read()),
            model="whisper-large-v3",
            response_format="verbose_json"
        )
    
    segments = []
    # verbose_json returns a list of segments
    if hasattr(transcription, 'segments') and transcription.segments:
        for seg in transcription.segments:
             segments.append({
                'start': seg.start,
                'end': seg.end,
                'text': seg.text.strip(),
                'original': seg.text.strip()
            })
    return segments

def transcribe_assemblyai(audio_path, api_key):
    """Fallback transcription using AssemblyAI"""
    try:
        import assemblyai as aai
    except ImportError:
        st.error("AssemblyAI library missing for fallback. pip install assemblyai")
        return []
        
    aai.settings.api_key = api_key
    transcriber = aai.Transcriber()
    config = aai.TranscriptionConfig(language_detection=True)
    transcript = transcriber.transcribe(audio_path, config=config)
    
    if transcript.error:
        st.error(f"AssemblyAI Error: {transcript.error}")
        return []
        
    segments = []
    for word_info in transcript.words:
        # Simple grouping into ~3 second chunks or based on punctuation
        # For a robust implementation, you'd want sentence-level grouping.
        # This is a simplified fallback grouping.
        pass
    
    # Using sentences if available, otherwise fallback to rough grouping
    if hasattr(transcript, 'get_sentences'):
        sentences = transcript.get_sentences()
        for s in sentences:
            segments.append({
                'start': s.start / 1000.0,
                'end': s.end / 1000.0,
                'text': s.text,
                'original': s.text
            })
    
    return segments

def translate_text(text, api_key, context="standard"):
    """Translate text using Gemini"""
    client = genai.Client(api_key=api_key)
    
    if context == "recap":
        prompt = f"""Translate the following text into natural-sounding, spoken Myanmar language (Burmese), suitable for a movie recap narrator. 
        It should flow well and sound exciting. Do not output anything other than the translation.
        Original: {text}"""
    else:
        prompt = f"""Translate the following text into natural-sounding, conversational Myanmar language (Burmese). 
        Make it suitable for voice acting/dubbing. Keep it concise. Do not output anything other than the translation.
        Original: {text}"""
        
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        st.warning(f"Translation failed for a segment: {e}")
        return text

def shorten_translation(original, current_translation, target_seconds, api_key):
    """Ask Gemini to shorten the translation to fit the time constraints"""
    client = genai.Client(api_key=api_key)
    prompt = f"""
    The following Myanmar translation is too long to be spoken in {target_seconds:.1f} seconds.
    Original English context: {original}
    Current Myanmar translation: {current_translation}
    
    Please provide a significantly shorter version of the Myanmar translation that conveys the core meaning but can be spoken quickly. 
    Output ONLY the shorter Myanmar text.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        return current_translation

async def generate_tts(text, output_path, voice="my-MM-ThihaNeural"):
    """Generate TTS using edge-tts"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    
def adjust_audio_speed(input_path, output_path, speed_factor):
    """Adjust audio duration using ffmpeg atempo filter"""
    # atempo is limited to 0.5 to 100.0. For factors outside, chain them.
    atempo_str = ""
    if speed_factor < 0.5:
        atempo_str = "atempo=0.5,atempo=" + str(speed_factor / 0.5)
    elif speed_factor > 100.0:
        atempo_str = "atempo=100.0,atempo=" + str(speed_factor / 100.0)
    else:
        atempo_str = f"atempo={speed_factor:.4f}"
        
    command = [
        "ffmpeg", "-y", "-i", input_path,
        "-filter:a", atempo_str,
        output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def process_segment_audio(idx, seg, temp_dir, api_keys, auto_shorten=True):
    """Generate TTS for a segment and adjust length to fit standard mode"""
    import asyncio
    
    tts_path = os.path.join(temp_dir, f"tts_{idx}.mp3")
    adjusted_path = os.path.join(temp_dir, f"adj_{idx}.mp3")
    
    # 1. Generate TTS
    text_to_speak = seg.get('translated', seg.get('text', ''))
    if not text_to_speak.strip():
        return None
        
    asyncio.run(generate_tts(text_to_speak, tts_path))
    
    if not os.path.exists(tts_path):
        return None
        
    # 2. Check length
    audio = AudioSegment.from_file(tts_path)
    audio_duration_sec = len(audio) / 1000.0
    target_duration = seg['end'] - seg['start']
    
    # 3. Handle Auto-shorten if TTS is way too long
    if auto_shorten and audio_duration_sec > target_duration * 1.5:
        shortened_text = shorten_translation(seg['original'], text_to_speak, target_duration, api_keys['gemini'])
        if shortened_text != text_to_speak:
            seg['translated'] = shortened_text  # Update state
            asyncio.run(generate_tts(shortened_text, tts_path))
            audio = AudioSegment.from_file(tts_path)
            audio_duration_sec = len(audio) / 1000.0

    # 4. Fit to segment (Standard Mode)
    if audio_duration_sec > 0 and target_duration > 0:
        speed_factor = audio_duration_sec / target_duration
        # Only adjust if difference is significant
        if abs(1.0 - speed_factor) > 0.05:
            adjust_audio_speed(tts_path, adjusted_path, speed_factor)
            return adjusted_path
            
    return tts_path

def create_final_dub_audio(segments, original_audio_path, temp_dir):
    """Combine generated TTS clips into a single audio file matching video length"""
    original = AudioSegment.from_file(original_audio_path)
    final_audio = AudioSegment.silent(duration=len(original))
    
    for idx, seg in enumerate(segments):
        audio_file = seg.get('audio_file')
        if audio_file and os.path.exists(audio_file):
            seg_audio = AudioSegment.from_file(audio_file)
            start_ms = int(seg['start'] * 1000)
            final_audio = final_audio.overlay(seg_audio, position=start_ms)
            
    final_audio_path = os.path.join(temp_dir, "final_dub.mp3")
    final_audio.export(final_audio_path, format="mp3")
    return final_audio_path

def mux_audio_video(video_path, audio_path, output_path):
    """Replace video audio track with the new dub track"""
    command = [
        "ffmpeg", "-y", "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        output_path
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def render_recap_video(segments, video_path, temp_dir):
    """Recap mode: Adjust video segments speed to match natural TTS length"""
    # This is a complex ffmpeg operation. We'll split the video into segments, 
    # change the speed of each video segment to match the audio, and concat.
    
    concat_file_path = os.path.join(temp_dir, "concat.txt")
    final_video_path = os.path.join(temp_dir, "final_recap.mp4")
    
    with open(concat_file_path, 'w') as f:
        for idx, seg in enumerate(segments):
            audio_file = seg.get('audio_file')
            if not audio_file or not os.path.exists(audio_file):
                continue
                
            orig_duration = seg['end'] - seg['start']
            audio = AudioSegment.from_file(audio_file)
            new_duration = len(audio) / 1000.0
            
            # Extract video segment
            seg_video = os.path.join(temp_dir, f"v_{idx}.mp4")
            ext_cmd = [
                "ffmpeg", "-y", "-ss", str(seg['start']), "-t", str(orig_duration),
                "-i", video_path, "-c", "copy", seg_video
            ]
            subprocess.run(ext_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Adjust video speed (setpts)
            # pts multiplier = new_duration / orig_duration
            adj_video = os.path.join(temp_dir, f"v_adj_{idx}.mp4")
            pts_mult = new_duration / orig_duration
            
            adj_cmd = [
                "ffmpeg", "-y", "-i", seg_video, 
                "-filter:v", f"setpts={pts_mult}*PTS",
                "-c:a", "copy", # we will mux audio later or add it here
                adj_video
            ]
            subprocess.run(adj_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # We need to multiplex the specific TTS audio into this adjusted video segment
            muxed_seg = os.path.join(temp_dir, f"mux_{idx}.mp4")
            mux_cmd = [
                 "ffmpeg", "-y", "-i", adj_video, "-i", audio_file,
                "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
                muxed_seg
            ]
            subprocess.run(mux_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            f.write(f"file '{muxed_seg}'\n")

    # Concat all segments
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_file_path,
        "-c", "copy", final_video_path
    ]
    subprocess.run(concat_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return final_video_path

def run_narrator_mode(video_path, api_key, temp_dir):
    """Extract frames and use Gemini Vision to write a recap script"""
    import base64
    st.info("Extracting frames for Scene analysis...")
    
    # Extract a frame every 5 seconds
    frames_dir = os.path.join(temp_dir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    
    cmd = [
        "ffmpeg", "-y", "-i", video_path, 
        "-vf", "fps=1/5", f"{frames_dir}/thumb%04d.jpg"
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    frames = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    
    if not frames:
        st.error("Failed to extract frames.")
        return []

    st.info(f"Analying {len(frames)} frames with Gemini...")
    client = genai.Client(api_key=api_key)
    
    # Due to token limits, we might process in batches, but for simplicity we'll take a subset if too many
    max_frames = 15
    if len(frames) > max_frames:
        step = len(frames) // max_frames
        frames = frames[::step][:max_frames]

    contents = []
    for frame_path in frames:
        contents.append(
             types.Part.from_bytes(
                data=open(frame_path, "rb").read(),
                mime_type="image/jpeg",
            )
        )
        
    prompt = """
    You are a movie recap narrator speaking to a Myanmar audience.
    Analyze these sequential frames from a video. 
    Write a concise, engaging recap script in Myanmar language (Burmese) describing the events in the third person.
    Format your response as a JSON array of objects, where each object represents a segment of the narration.
    Example format:
    [
      {"start": 0.0, "end": 5.0, "text": "ဒီရုပ်ရှင်လေးကတော့..." },
      {"start": 5.0, "end": 10.0, "text": "အဓိကဇာတ်ကောင်ဟာ အခန်းထဲဝင်လာပြီး..." }
    ]
    Ensure the start and end times roughly align with the chronological progression of the images (assume each image represents a 5 second interval).
    Respond ONLY with valid JSON.
    """
    contents.append(prompt)
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
        )
        
        # Parse JSON
        resp_text = response.text.strip()
        if resp_text.startswith("```json"):
            resp_text = resp_text[7:-3]
        
        script_data = json.loads(resp_text)
        
        # Format for our pipeline
        segments = []
        for item in script_data:
            segments.append({
                'start': float(item.get('start', 0)),
                'end': float(item.get('end', 0)),
                'original': 'Narrator script generated by AI',
                'text': item.get('text', ''),
                'translated': item.get('text', '') # Already in Myanmar
            })
        return segments
        
    except Exception as e:
        st.error(f"Narrator generation failed: {e}")
        return []

def generate_srt(segments):
    """Generate SRT file content"""
    subs = []
    for i, seg in enumerate(segments, start=1):
        start = timedelta(seconds=seg['start'])
        end = timedelta(seconds=seg['end'])
        text = seg.get('translated', seg.get('text', ''))
        subs.append(srt.Subtitle(index=i, start=start, end=end, content=text))
    return srt.compose(subs)

st.title("Spidy Dub Studio 🎬🎙️")

# File Upload
uploaded_file = st.file_uploader("Upload MP4 Video", type=["mp4"])
if uploaded_file is not None and st.session_state.flow_state == 'init':
    st.session_state.video_path = os.path.join(st.session_state.temp_dir, "input.mp4")
    with open(st.session_state.video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.session_state.audio_path = os.path.join(st.session_state.temp_dir, "input_audio.mp3")
    
    with st.spinner("Extracting Audio..."):
        extract_audio(st.session_state.video_path, st.session_state.audio_path)
        
    if mode == "Narrator Mode":
        st.session_state.flow_state = 'translating' # Skip whisper, go to vision analysis
    else:
        st.session_state.flow_state = 'ready_transcribe'
    st.rerun()

if st.session_state.flow_state == 'ready_transcribe':
    st.subheader("Step 1: Speech to Text")
    if st.button("Start Transcription (Whisper)"):
        if not st.session_state.api_keys['groq']:
            st.error("Groq API Key is required for standard transcription.")
        else:
            with st.spinner("Transcribing with Groq Whisper..."):
                try:
                    segments = transcribe_groq(st.session_state.audio_path, st.session_state.api_keys['groq'])
                    
                    if auto_merge:
                        segments = merge_short_segments(segments)
                        
                    st.session_state.segments = segments
                    st.session_state.flow_state = 'transcribed'
                    st.rerun()
                except Exception as e:
                    if "403" in str(e) and use_aai_fallback and st.session_state.api_keys['assemblyai']:
                        st.warning("Groq API blocked (403). Falling back to AssemblyAI...")
                        segments = transcribe_assemblyai(st.session_state.audio_path, st.session_state.api_keys['assemblyai'])
                        if segments:
                            if auto_merge:
                                segments = merge_short_segments(segments)
                            st.session_state.segments = segments
                            st.session_state.flow_state = 'transcribed'
                            st.rerun()
                    else:
                        st.error(f"Transcription failed: {e}")

if st.session_state.flow_state == 'transcribed' or (mode == "Narrator Mode" and st.session_state.flow_state == 'translating'):
    st.subheader("Step 2: Translation & Scripting")
    
    if mode == "Narrator Mode" and not st.session_state.segments:
         if not st.session_state.api_keys['gemini']:
             st.error("Gemini API Key is required for Narrator Mode.")
         else:
             if st.button("Generate Narrator Script with Gemini Vision"):
                 with st.spinner("Analyzing video scenes..."):
                     segments = run_narrator_mode(st.session_state.video_path, st.session_state.api_keys['gemini'], st.session_state.temp_dir)
                     if segments:
                         st.session_state.segments = segments
                         st.session_state.flow_state = 'translated' # Already in Myanmar
                         st.rerun()
                         
    elif st.session_state.segments:
        st.write(f"Found {len(st.session_state.segments)} segments.")
        if st.button("Translate to Myanmar"):
            if not st.session_state.api_keys['gemini']:
                st.error("Gemini API Key is required for translation.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                context_mode = "recap" if mode == "Recap Studio" else "standard"
                
                for i, seg in enumerate(st.session_state.segments):
                    status_text.text(f"Translating segment {i+1}/{len(st.session_state.segments)}...")
                    translated = translate_text(seg['text'], st.session_state.api_keys['gemini'], context_mode)
                    st.session_state.segments[i]['translated'] = translated
                    progress_bar.progress((i + 1) / len(st.session_state.segments))
                    time.sleep(0.5) # Rate limit padding
                    
                st.session_state.flow_state = 'translated'
                st.rerun()

if st.session_state.flow_state in ['translated', 'generated', 'merged']:
    st.subheader("Step 3: Review and Edit Subtitles")
    
    with st.expander("Edit Translations (Click to expand)", expanded=True):
        for i, seg in enumerate(st.session_state.segments):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.caption(f"[{seg['start']:.1f}s - {seg['end']:.1f}s]")
                st.write(seg.get('original', seg.get('text', '')))
            with col2:
                # Store edit directly into state
                st.session_state.segments[i]['translated'] = st.text_area(
                    "Myanmar Text", 
                    value=seg.get('translated', ''), 
                    key=f"edit_{i}",
                    height=70,
                    label_visibility="collapsed"
                )
                
    if st.session_state.flow_state == 'translated':
        if st.button("Generate Audio (TTS)", type="primary"):
            st.session_state.flow_state = 'generating'
            st.rerun()

if st.session_state.flow_state == 'generating':
    st.subheader("Step 4: Generating Voices")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, seg in enumerate(st.session_state.segments):
        status_text.text(f"Generating TTS for segment {i+1}/{len(st.session_state.segments)}...")
        
        # In Recap mode, we don't strictly constrain to target length here, we do it in video render
        should_shorten = auto_shorten if mode == "Standard Dub" else False
        
        audio_file = process_segment_audio(i, seg, st.session_state.temp_dir, st.session_state.api_keys, auto_shorten=should_shorten)
        st.session_state.segments[i]['audio_file'] = audio_file
        progress_bar.progress((i + 1) / len(st.session_state.segments))
        
    st.session_state.flow_state = 'generated'
    st.rerun()

if st.session_state.flow_state == 'generated':
    st.subheader("Step 5: Render Final Video")
    
    if st.button("Merge Audio and Video", type="primary"):
        with st.spinner("Rendering final output..."):
            if mode == "Recap Studio":
                st.info("Applying Recap Studio logic (adjusting video speed to match audio)...")
                final_video = render_recap_video(st.session_state.segments, st.session_state.video_path, st.session_state.temp_dir)
                st.session_state.final_video_path = final_video
            else:
                # Standard or Narrator without dynamic speed adjustment
                st.info("Creating master dub track...")
                final_audio = create_final_dub_audio(st.session_state.segments, st.session_state.audio_path, st.session_state.temp_dir)
                
                st.info("Muxing audio to video...")
                final_video = os.path.join(st.session_state.temp_dir, "final_dubbed.mp4")
                mux_audio_video(st.session_state.video_path, final_audio, final_video)
                st.session_state.final_video_path = final_video
            
            # Generate SRT
            srt_content = generate_srt(st.session_state.segments)
            srt_path = os.path.join(st.session_state.temp_dir, "subtitles.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            st.session_state.srt_path = srt_path
                
            st.session_state.flow_state = 'merged'
            st.rerun()

if st.session_state.flow_state == 'merged':
    st.subheader("🎉 Done! Download your files")
    
    col1, col2 = st.columns(2)
    with col1:
        if os.path.exists(st.session_state.final_video_path):
            with open(st.session_state.final_video_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Dubbed Video (MP4)",
                    data=f,
                    file_name="spidy_dub_output.mp4",
                    mime="video/mp4",
                    type="primary"
                )
    with col2:
         if 'srt_path' in st.session_state and os.path.exists(st.session_state.srt_path):
             with open(st.session_state.srt_path, "rb") as f:
                 st.download_button(
                    label="⬇️ Download Subtitles (SRT)",
                    data=f,
                    file_name="subtitles.srt",
                    mime="text/plain"
                 )
                 
    # Cleanup hint
    st.info("Click 'Reset Session' in the sidebar to start a new project and clear temporary files.")

# Add simple footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: gray; font-size: small;'>Spidy Dub Studio — Powered by Streamlit, Groq, Gemini, and Edge TTS</div>", unsafe_allow_html=True)
```

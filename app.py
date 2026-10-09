#!/usr/bin/env python3
"""Audio Dub Studio — ဗီဒီယိုထဲက စာသားပြောအပိုင်းတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးတဲ့ tool.

RecapKit ရဲ့ Audio Dub feature ကို တစ်ယောက်စာသုံးဖို့ ပြန်ဆောက်ထားတာ။
Login မလို၊ ငွေမလို — ကိုယ့် Streamlit Cloud မှာ run တယ်။
API key တွေကို browser localStorage မှာ မှတ်ထားတယ် — တစ်ခါထည့်ရုံနဲ့
hard refresh ဆွဲလည်း မပျောက်ဘူး (server Secrets ရှိရင် အဲ့ဒါက အဓိက)။

Pipeline:
  1. MP4 တင် → ffmpeg နဲ့ audio ထုတ် (mp3 16k mono, 32k — Groq 25MB ကန့်သတ်ချက်နဲ့ကိုက်အောင်)
  2. Groq Whisper API (whisper-large-v3) နဲ့ စာသားထုတ် (timestamp ပါ)
  3. Gemini နဲ့ သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ဘာသာပြန်
  4. ပြန်စစ်ပြီး ပြင်လို့ရ (တစ်ကြောင်းချင်း)
  5. edge-tts (my-MM-ThihaNeural) နဲ့ အသံထုတ်
  6. ဗီဒီယိုအသစ်နဲ့ ပေါင်း → MP4 download + Speed 2x ထိ တင်လို့ရ
  7. Social Media အတွက် Viral Caption (3Sec Hook) + English Hashtags ၅ ခုထုတ်ပေးခြင်း

Run:  streamlit run app.py
"""
import asyncio
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import uuid
import tempfile
import streamlit as st
import google.generativeai as genai
from groq import Groq
import edge_tts

st.set_page_config(page_title="Audio Dub Studio", page_icon="🕷️", layout="wide")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_TTS = os.path.join(APP_DIR, "cache_tts")
WORK_DIR = os.path.join(APP_DIR, "work")
os.makedirs(CACHE_TTS, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

# ---------------------------------------------------------- 🕷️ Spider-Man theme
_SPIDEY_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&display=swap');

/* --- နောက်ခံ: ညမှောင် + spider web --- */
.stApp {
    background-color: #0A0A14;
    background-image:
        url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260' viewBox='0 0 260 260'%3E%3Cg fill='none' stroke='%23E62429' stroke-opacity='0.06'%3E%3Ccircle cx='260' cy='0' r='55'/%3E%3Ccircle cx='260' cy='0' r='105'/%3E%3Ccircle cx='260' cy='0' r='155'/%3E%3Ccircle cx='260' cy='0' r='205'/%3E%3Cpath d='M260 0 L0 260 M260 0 L90 260 M260 0 L175 260 M260 0 L260 260 M260 0 L0 175 M260 0 L0 90'/%3E%3C/g%3E%3C/svg%3E"),
        radial-gradient(1000px 480px at 88% -5%, rgba(230,36,41,.12), transparent 60%),
        radial-gradient(820px 520px at 4% 108%, rgba(43,92,230,.12), transparent 60%);
    background-repeat: no-repeat;
    background-position: top right;
}

/* --- hero --- */
.spidey-hero { text-align: center; padding: 20px 0 4px; }
.spidey-kicker { color: #8A93B8; font-size: .78rem; letter-spacing: 3px; font-weight: 700; }
.spidey-title {
    font-family: 'Bangers', 'Arial Black', sans-serif;
    font-size: 3.2rem; letter-spacing: 3px; color: #F03A3A;
    -webkit-text-stroke: 1.5px #5d0a0d;
    text-shadow: 3px 3px 0 #1D4ED8, 7px 7px 0 rgba(0,0,0,.55), 0 0 34px rgba(230,36,41,.55);
    transform: rotate(-1.5deg); margin: 2px 0;
}
.spidey-sub { color: #B9C4E8; font-size: 1rem; margin-top: 8px; }
@media (max-width: 640px){ .spidey-title{ font-size: 2.2rem; } }

/* --- အဆင့်ခြေရာ (step tracker) --- */
.spidey-steps { display: flex; gap: 8px; margin: 16px 0 6px; flex-wrap: wrap; }
.spidey-step { flex: 1 1 0; min-width: 96px; text-align: center; padding: 9px 4px;
    border-radius: 14px; font-size: .8rem; font-weight: 700;
    background: rgba(255,255,255,.045); border: 1px solid rgba(255,255,255,.13); color: #9AA0BC; }
.spidey-step .n { display: block; font-size: 1.1rem; margin-bottom: 2px; }
.spidey-step.done { background: rgba(230,36,41,.16); border-color: rgba(230,36,41,.7); color: #FFB4B6; }
.spidey-step.current { background: linear-gradient(135deg,#E62429,#9E1116); color: #fff;
    border-color: #FF7A7A; box-shadow: 0 0 18px rgba(230,36,41,.65); }
.spidey-step.skip { opacity: .4; }

/* --- ကတ် (st.container(border=True) အစစ် — အထဲမှာ content တကယ်ရှိတယ်) --- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(18,18,36,.78);
    border: 1px solid rgba(230,36,41,.30) !important;
    border-radius: 18px;
    box-shadow: 0 8px 28px rgba(0,0,0,.5);
}
.spidey-stephead {
    display: flex; align-items: center; gap: 12px;
    padding: 10px 16px; margin-bottom: 6px;
    background: linear-gradient(90deg, rgba(230,36,41,.25), rgba(43,92,230,.14));
    border: 1px solid rgba(230,36,41,.28);
    border-radius: 12px;
    font-size: 1.12rem; font-weight: 800; color: #fff;
}
.spidey-num { width: 34px; height: 34px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg,#F03A3A,#8f1013); color: #fff;
    font-weight: 800; font-size: 1.05rem; box-shadow: 0 0 14px rgba(230,36,41,.8); }

/* --- ခလုတ် --- */
div[data-testid*="stBaseButton-primary"] > button, .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #F03A3A, #A50F14) !important;
    color: #fff !important; border: none !important; border-radius: 12px !important;
    font-weight: 800 !important; letter-spacing: .3px;
    box-shadow: 0 4px 20px rgba(230,36,41,.5) !important;
}
div[data-testid*="stBaseButton-primary"] > button:hover, .stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 28px rgba(230,36,41,.85) !important;
    transform: translateY(-1px); color: #fff !important;
}
.stButton > button[kind="secondary"], div[data-testid*="stBaseButton-secondary"] > button {
    border: 1px solid rgba(80,120,255,.55) !important; border-radius: 12px !important;
    background: rgba(43,92,230,.10) !important; color: #C9D6FF !important; font-weight: 700 !important;
}
.stButton > button[kind="secondary"]:hover, div[data-testid*="stBaseButton-secondary"] > button:hover {
    background: rgba(43,92,230,.22) !important; color: #fff !important;
    box-shadow: 0 0 16px rgba(43,92,230,.45) !important; border-color: #7FA2FF !important;
}

/* --- sidebar --- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #160709 0%, #0A0A14 70%) !important;
    border-right: 1px solid rgba(230,36,41,.32);
}
section[data-testid="stSidebar"] h3 { border-left: 4px solid #E62429; padding-left: 10px !important; }
section[data-testid="stSidebar"] h4 { color: #FF8A8D !important; }

/* --- တခြား --- */
div[data-testid="stExpander"] { border: 1px solid rgba(230,36,41,.32); border-radius: 14px;
    background: rgba(230,36,41,.05); }
div[data-testid="stFileUploader"] { border: 1.5px dashed rgba(230,36,41,.55); border-radius: 16px;
    background: rgba(230,36,41,.05); padding: 10px; }
div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus {
    border-color: #E62429 !important;
    box-shadow: 0 0 0 1px #E62429, 0 0 14px rgba(230,36,41,.4) !important; }
div[data-testid="stProgress"] > div > div { box-shadow: 0 0 12px rgba(230,36,41,.8); }
.spidey-dl-label { font-weight: 800; color: #FFB4B6; margin: 6px 0 10px; font-size: 1rem; }
.spidey-foot { text-align: center; color: #5A6080; font-size: .8rem; padding: 20px 0 8px; }

/* wizard nav fix */
div[data-testid="stHorizontalBlock"]:has(> :nth-child(6):last-child) {
    flex-wrap: nowrap !important;
    gap: 0.25rem !important;
}
div[data-testid="stHorizontalBlock"]:has(> :nth-child(6):last-child) > div {
    min-width: 0 !important;
}
div[data-testid="stHorizontalBlock"]:has(> :nth-child(6):last-child) button {
    padding-left: 0.2rem !important;
    padding-right: 0.2rem !important;
}
.wiz-bnav-col { display: none; }
div[data-testid="stElementContainer"]:has(.wiz-bnav-col) { display: none; }
div[data-testid="stHorizontalBlock"]:has(.wiz-bnav-col) {
    flex-wrap: nowrap !important;
    gap: 0.5rem !important;
}
div[data-testid="stHorizontalBlock"]:has(.wiz-bnav-col) > div {
    min-width: 0 !important;
}
</style>"""

st.markdown(_SPIDEY_CSS, unsafe_allow_html=True)

_card_ctx_stack = []

def _spidey_card_open(n, title):
    if _card_ctx_stack:
        _card_ctx_stack.clear()
    ctx = st.container(border=True)
    ctx.__enter__()
    _card_ctx_stack.append(ctx)
    st.markdown(
        f'<div class="spidey-stephead"><span class="spidey-num">{n}</span>'
        f"<span>{title}</span></div>",
        unsafe_allow_html=True,
    )

def _spidey_card_close():
    if _card_ctx_stack:
        ctx = _card_ctx_stack.pop()
        ctx.__exit__(None, None, None)

def _spidey_steps(current_step):
    steps = ["Upload", "Transcribe", "Translate", "TTS", "Render", "Social"]
    html = '<div class="spidey-steps">'
    for i, name in enumerate(steps):
        s_class = "spidey-step"
        if i < current_step: s_class += " done"
        elif i == current_step: s_class += " current"
        else: s_class += " skip"
        html += f'<div class="{s_class}"><span class="n">{i+1}</span>{name}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def run_cmd(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        st.error(f"Command Error: {result.stderr.decode('utf-8')}")
    return result.returncode == 0

async def generate_edge_tts(text, output_path):
    communicate = edge_tts.Communicate(text, "my-MM-ThihaNeural")
    await communicate.save(output_path)

def extract_audio(video_path, audio_path):
    cmd = ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-ac", "1", "-ar", "16000", "-q:a", "2", audio_path]
    return run_cmd(cmd)

def transcribe_audio_groq(audio_path, api_key):
    client = Groq(api_key=api_key)
    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
          file=(audio_path, file.read()),
          model="whisper-large-v3",
          response_format="json",
        )
    return transcription.text

def translate_script_gemini(text, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"Translate the following text to natural, spoken Myanmar (Burmese) language:\n\n{text}"
    response = model.generate_content(prompt)
    return response.text

def generate_social_media_pack(script, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = f"""
    You are an expert social media manager. Based on the following video script, create:
    1. A highly engaging, viral 3-second hook and caption in Myanmar language (can mix a bit of English if natural).
    2. Exactly 5 trending English hashtags relevant to the content.
    
    Format the output strictly as:
    [Caption]
    <Your caption here>
    
    [Hashtags]
    <#hashtag1 #hashtag2 #hashtag3 #hashtag4 #hashtag5>
    
    Script:
    {script}
    """
    response = model.generate_content(prompt)
    return response.text

if "step" not in st.session_state: st.session_state.step = 0
if "video_path" not in st.session_state: st.session_state.video_path = None
if "audio_path" not in st.session_state: st.session_state.audio_path = None
if "transcription" not in st.session_state: st.session_state.transcription = ""
if "translation" not in st.session_state: st.session_state.translation = ""
if "dub_audio_path" not in st.session_state: st.session_state.dub_audio_path = None
if "final_video_path" not in st.session_state: st.session_state.final_video_path = None
if "social_pack" not in st.session_state: st.session_state.social_pack = None

with st.sidebar:
    st.markdown('<h2 style="color: #F03A3A; font-family: Bangers;">🕷️ API Keys</h2>', unsafe_allow_html=True)
    groq_key = st.text_input("Groq API Key (Whisper)", type="password")
    gemini_key = st.text_input("Gemini API Key (Translate & Caption)", type="password")
    st.markdown("---")
    if st.button("Reset Process"):
        st.session_state.clear()
        st.rerun()

st.markdown('<div class="spidey-hero"><div class="spidey-kicker">SPIDER-VERSE TECH</div><div class="spidey-title">Audio Dub Studio</div><div class="spidey-sub">AI Myanmar Dubbing & Social Media Engine</div></div>', unsafe_allow_html=True)

_spidey_steps(st.session_state.step)

if st.session_state.step == 0:
    _spidey_card_open(1, "Upload Video")
    uploaded_file = st.file_uploader("Upload MP4 Video", type=["mp4"])
    if uploaded_file is not None:
        if st.button("Next: Process Video", type="primary"):
            video_path = os.path.join(WORK_DIR, "input.mp4")
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.video_path = video_path
            st.session_state.step = 1
            st.rerun()
    _spidey_card_close()

elif st.session_state.step == 1:
    _spidey_card_open(2, "Extract & Transcribe")
    if not groq_key:
        st.warning("Please enter your Groq API Key in the sidebar.")
    else:
        if st.button("Start Transcription", type="primary"):
            with st.spinner("Extracting audio..."):
                audio_path = os.path.join(WORK_DIR, "audio.mp3")
                if extract_audio(st.session_state.video_path, audio_path):
                    st.session_state.audio_path = audio_path
            
            with st.spinner("Transcribing with Groq Whisper..."):
                try:
                    text = transcribe_audio_groq(st.session_state.audio_path, groq_key)
                    st.session_state.transcription = text
                    st.session_state.step = 2
                    st.rerun()
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
    if st.button("Back", key="b1"): st.session_state.step = 0; st.rerun()
    _spidey_card_close()

elif st.session_state.step == 2:
    _spidey_card_open(3, "Translate Script")
    st.text_area("Original Text", st.session_state.transcription, height=150, disabled=True)
    if not gemini_key:
        st.warning("Please enter your Gemini API Key in the sidebar.")
    else:
        if st.button("Translate to Myanmar", type="primary"):
            with st.spinner("Translating via Gemini..."):
                try:
                    translated = translate_script_gemini(st.session_state.transcription, gemini_key)
                    st.session_state.translation = translated
                    st.session_state.step = 3
                    st.rerun()
                except Exception as e:
                    st.error(f"Translation failed: {e}")
    if st.button("Back", key="b2"): st.session_state.step = 1; st.rerun()
    _spidey_card_close()

elif st.session_state.step == 3:
    _spidey_card_open(4, "Edit & Generate Dub")
    edited_text = st.text_area("Myanmar Script (Edit if needed)", st.session_state.translation, height=200)
    
    if st.button("Generate Myanmar Audio", type="primary"):
        st.session_state.translation = edited_text
        with st.spinner("Generating Voice with Edge-TTS..."):
            dub_path = os.path.join(WORK_DIR, "dubbed.mp3")
            asyncio.run(generate_edge_tts(edited_text, dub_path))
            st.session_state.dub_audio_path = dub_path
            st.session_state.step = 4
            st.rerun()
            
    if st.button("Back", key="b3"): st.session_state.step = 2; st.rerun()
    _spidey_card_close()

elif st.session_state.step == 4:
    _spidey_card_open(5, "Render Final Video")
    st.audio(st.session_state.dub_audio_path)
    
    st.markdown("### ⚡ Video Speed Adjustment")
    st.markdown("မြန်နှုန်းကို လိုသလိုချိန်ညှိနိုင်ပါတယ်။ (1.0 = ပုံမှန်, 2.0 = နှစ်ဆမြန်)")
    speed_factor = st.slider("Playback Speed", min_value=1.0, max_value=2.0, value=1.0, step=0.1)
    
    if st.button("Mix Audio & Render", type="primary"):
        with st.spinner(f"Rendering Video at {speed_factor}x speed..."):
            final_vid = os.path.join(WORK_DIR, "final_output.mp4")
            if speed_factor == 1.0:
                cmd = ["ffmpeg", "-y", "-i", st.session_state.video_path, "-i", st.session_state.dub_audio_path, 
                       "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", final_vid]
            else:
                v_pts = 1.0 / speed_factor
                a_tempo = speed_factor
                cmd = ["ffmpeg", "-y", "-i", st.session_state.video_path, "-i", st.session_state.dub_audio_path,
                       "-filter_complex", f"[0:v]setpts={v_pts}*PTS[v];[1:a]atempo={a_tempo}[a]", 
                       "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-c:a", "aac", final_vid]
            
            if run_cmd(cmd):
                st.session_state.final_video_path = final_vid
                st.session_state.step = 5
                st.rerun()
                
    if st.button("Back", key="b4"): st.session_state.step = 3; st.rerun()
    _spidey_card_close()

elif st.session_state.step == 5:
    _spidey_card_open(6, "Done! Social Media Pack")
    
    col1, col2 = st.columns(2)
    with col1:
        st.video(st.session_state.final_video_path)
        with open(st.session_state.final_video_path, "rb") as f:
            st.download_button("⬇️ Download Final Video", f, file_name="dubbed_video.mp4", mime="video/mp4", type="primary")
            
    with col2:
        st.markdown("### 🔥 Viral Caption & Hook")
        
        if st.session_state.social_pack is None:
            if not gemini_key:
                st.warning("Please provide Gemini API key in sidebar to generate caption.")
            else:
                with st.spinner("Writing 3-sec hook and finding hashtags..."):
                    try:
                        st.session_state.social_pack = generate_social_media_pack(st.session_state.translation, gemini_key)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to generate caption: {e}")
        else:
            st.text_area("Generated Caption & Hashtags", st.session_state.social_pack, height=250)
            
            # Try Again Button for Social Caption
            if st.button("🔄 Try Again (Regenerate)", type="secondary"):
                st.session_state.social_pack = None
                st.rerun()
                
    st.markdown("---")
    if st.button("Start New Video", key="b5"):
        st.session_state.clear()
        st.rerun()
    _spidey_card_close()

st.markdown('<div class="spidey-foot">Developed with 🕷️ Spidey Theme | Powered by Streamlit, FFmpeg, Groq & Gemini</div>', unsafe_allow_html=True)

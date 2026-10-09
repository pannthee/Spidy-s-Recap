#!/usr/bin/env python3
"""Spidy Dub Studio — All-in-One AI Studio
(Auto Transcript + Text-to-Speech Generator + Video Dubbing + Thumbnail Maker)
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
import base64
import requests
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_TTS = os.path.join(APP_DIR, "cache_tts")
WORK_DIR = os.path.join(APP_DIR, "work")
os.makedirs(CACHE_TTS, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

# ---------------------------------------------------------- 🕷️ UI Styling
_SPIDEY_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&display=swap');
.stApp {
    background-color: #0A0A14;
    background-image:
        radial-gradient(1000px 480px at 88% -5%, rgba(230,36,41,.12), transparent 60%),
        radial-gradient(820px 520px at 4% 108%, rgba(43,92,230,.12), transparent 60%);
}
.spidey-hero { text-align: center; padding: 15px 0 6px; }
.spidey-kicker { color: #8A93B8; font-size: .78rem; letter-spacing: 3px; font-weight: 700; }
.spidey-title {
    font-family: 'Bangers', 'Arial Black', sans-serif;
    font-size: 3rem; letter-spacing: 2px; color: #F03A3A;
    text-shadow: 2px 2px 0 #1D4ED8, 5px 5px 0 rgba(0,0,0,.55);
    margin: 2px 0;
}
.spidey-sub { color: #B9C4E8; font-size: 0.95rem; margin-top: 4px; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(18,18,36,.78);
    border: 1px solid rgba(230,36,41,.30) !important;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,.5);
}
.spidey-stephead {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 14px; margin-bottom: 8px;
    background: linear-gradient(90deg, rgba(230,36,41,.25), rgba(43,92,230,.14));
    border: 1px solid rgba(230,36,41,.28);
    border-radius: 10px; font-size: 1.05rem; font-weight: 800; color: #fff;
}
.spidey-num {
    width: 30px; height: 30px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg,#F03A3A,#8f1013); color: #fff; font-weight: 800;
}
button[kind="primary"] {
    background: linear-gradient(135deg, #F03A3A, #A50F14) !important;
    color: #fff !important; border-radius: 10px !important; font-weight: 800 !important;
}
</style>"""

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3"
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
VOICE_MALE = "my-MM-ThihaNeural"
VOICE_FEMALE = "my-MM-NilarNeural"

_DEFAULT_PRON_DICT = [
    {"word": "AI", "replace": "အေအိုင်"},
    {"word": "Crypto", "replace": "ခရစ်ပတို"},
    {"word": "Delight", "replace": "ဒီလိုက်"},
    {"word": "Recap", "replace": "ရီကပ်"}
]

# ------------------------------------------------------------------ Helper functions
def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

def dur(path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", path], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0

def fmt_ts(sec):
    total_ms = max(0, int(round(sec * 1000)))
    h, rem = divmod(total_ms, 3600000)
    m, rem = divmod(rem, 60000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def silence(path, seconds, sr=24000):
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "anullsrc=r=24000:cl=mono", "-t", f"{seconds:.3f}",
         "-ar", str(sr), path])

def apply_pronunciation(text, dict_list):
    res = text
    for item in dict_list:
        w, r = item.get("word", "").strip(), item.get("replace", "").strip()
        if w and r:
            res = re.sub(re.escape(w), r, res, flags=re.IGNORECASE)
    return res

def segments_to_srt(segments):
    return "\n".join([f"{i}\n{fmt_ts(s['start'])} --> {fmt_ts(s['end'])}\n{s['text']}\n" for i, s in enumerate(segments, 1)])

def generate_proportional_srt(text, total_duration):
    """စာသားကို အပိုင်းပိုင်းခွဲပြီး စုစုပေါင်းကြာချိန်အလိုက် အချိုးကျ SRT ထုတ်ပေးခြင်း"""
    clean_text = re.sub(r'\s+', ' ', text).strip()
    segments = [s.strip() for s in re.split(r'(?<=[။!?\n])', clean_text) if s.strip()]
    if not segments:
        segments = [text]
    total_chars = sum(len(s) for s in segments) or 1
    srt_list, current_time = [], 0.0
    for s in segments:
        seg_dur = (len(s) / total_chars) * total_duration
        end_time = current_time + seg_dur
        srt_list.append({"start": current_time, "end": end_time, "text": s})
        current_time = end_time
    return segments_to_srt(srt_list)

# ------------------------------------------------------- Gemini APIs
def _gemini_call(api_key, model_id, system_text, payload_text, json_mode=True):
    url = f"{GEMINI_BASE}{model_id}:generateContent"
    cfg = {"temperature": 0.3, "maxOutputTokens": 8192}
    if json_mode:
        cfg["responseMimeType"] = "application/json"
    body = {
        "contents": [{"role": "user", "parts": [{"text": system_text}, {"text": payload_text}]}],
        "generationConfig": cfg
    }
    r = requests.post(url, headers={"Content-Type": "application/json", "x-goog-api-key": api_key}, json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini error {r.status_code}: {r.text[:250]}")
    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    if json_mode:
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt)
        return json.loads(txt.strip())
    return txt

def gemini_generate_transcript(api_key, model_id, raw_transcript, duration_pref="1"):
    """Auto Transcript: မူရင်းစာသားမှ ဇာတ်လမ်းနှင့် ခေါင်းစဉ်များ ဖန်တီးပေးခြင်း"""
    dur_map = {
        "1": "~250 words suitable for 1 minute reading",
        "2": "~400 words suitable for 2 minutes reading",
        "3": "~600 words suitable for 3 minutes reading",
        "5": "~900 words suitable for 5 minutes reading"
    }
    req_dur = dur_map.get(duration_pref, "~300 words")
    sys_prompt = (
        f"You are a professional movie recap & viral scriptwriter. Read the raw transcription and create an engaging storytelling script in SPOKEN BURMESE (MYANMAR). "
        f"The script must be {req_dur}. "
        f"Also generate 5 clickbaity Burmese titles (each title MUST end with exactly 4 relevant hashtags).\n"
        f"Return ONLY valid JSON with keys 'titles' (list of strings) and 'script' (string)."
    )
    return _gemini_call(api_key, model_id, sys_prompt, raw_transcript[:12000], json_mode=True)

# ------------------------------------------------------- Groq STT
def transcribe_audio_groq(audio_path, api_key, language=None):
    with open(audio_path, "rb") as f:
        data = f.read()
    files = {"file": (os.path.basename(audio_path), data, "audio/mpeg")}
    form = {"model": GROQ_MODEL, "response_format": "verbose_json"}
    if language:
        form["language"] = language
    r = requests.post(GROQ_URL, headers={"Authorization": f"Bearer {api_key}"}, files=files, data=form, timeout=300)
    if r.status_code != 200:
        raise RuntimeError(f"Groq error: {r.text[:200]}")
    segs = []
    for s in (r.json().get("segments") or []):
        t = (s.get("text") or "").strip()
        if t:
            segs.append({"start": float(s.get("start") or 0), "end": float(s.get("end") or 0), "text": t})
    return segs

# ------------------------------------------------------- Edge-TTS
async def _edge_save(text, voice, path):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(path)

def tts_generate_file(text, voice, out_path):
    asyncio.run(_edge_save(text, voice, out_path))
    return out_path

# ------------------------------------------------------- Main Application
def main():
    st.set_page_config(page_title="Spidy Dub Studio", page_icon="🕷️", layout="wide")
    st.markdown(_SPIDEY_CSS, unsafe_allow_html=True)

    if "pron_dict" not in st.session_state:
        st.session_state.pron_dict = _DEFAULT_PRON_DICT.copy()

    # Sidebar Controls
    with st.sidebar:
        st.markdown("### 🕷️ Spidey Control")
        st.markdown("#### 🔑 API Keys")
        gemini_key = st.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
        groq_key = st.text_input("Groq API Key", value=os.environ.get("GROQ_API_KEY", ""), type="password")

        st.divider()
        st.markdown("#### 🗣️ အသံ ဆက်တင်")
        voice = st.selectbox("အသံရွေးချယ်ပါ", [VOICE_MALE, VOICE_FEMALE],
                             format_func=lambda v: "🗣️ ကျား (Thiha)" if v == VOICE_MALE else "🗣️ မ (Nilar)")

        st.divider()
        with st.expander("📖 အသံထွက် အဘိဓာန် (Pronunciation)", expanded=False):
            st.caption("AI အသံထွက်မှားတတ်သော စာလုံးများကို အစားထိုးသတ်မှတ်ပါ:")
            new_w = st.text_input("မူရင်းစာလုံး (Word)", key="pw_w")
            new_r = st.text_input("အသံထွက်စာ (Replace)", key="pw_r")
            if st.button("➕ ထည့်ရန်"):
                if new_w and new_r:
                    st.session_state.pron_dict.append({"word": new_w, "replace": new_r})
                    st.success("ထည့်သွင်းပြီးပါပြီ!")
            st.write(st.session_state.pron_dict)

    # Header
    st.markdown(
        '<div class="spidey-hero">'
        '<div class="spidey-kicker">🕸️ ALL-IN-ONE VIDEO CREATOR STUDIO 🕸️</div>'
        '<div class="spidey-title">Spidy Dub Studio</div>'
        '<div class="spidey-sub">Auto Transcript • အသံဖန်တီးမည် • Video Dubbing 🕷️</div>'
        '</div>', unsafe_allow_html=True
    )

    # TABS Definition
    tab_gen, tab_transcript = st.tabs([
        "🔊 အသံဖန်တီးမည် (Generator)",
        "✨ Auto Transcript Studio"
    ])

    # =========================================================================
    # TAB 1: အသံဖန်တီးမည် (TTS Generator)
    # =========================================================================
    with tab_gen:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">1</span><span>စာသားမှ မြန်မာအသံဖိုင် ဖန်တီးမည်</span></div>', unsafe_allow_html=True)
        gen_text = st.text_area("အသံဖန်တီးလိုသော စာသားကို ရိုက်ထည့်ပါ:", height=250, placeholder="မင်္ဂလာပါ... ဒီနေရာတွင် အသံသွင်းလိုသော မြန်မာစာသားများကို ရိုက်ထည့်ပါ...")

        col_g1, col_g2 = st.columns([1, 1])
        with col_g1:
            if st.button("🔍 အစမ်းနားထောင်မည် (Preview)", use_container_width=True):
                if not gen_text.strip():
                    st.warning("စာသားအရင် ရိုက်ထည့်ပေးပါ")
                else:
                    preview_text = apply_pronunciation(gen_text[:120], st.session_state.pron_dict)
                    p_path = os.path.join(WORK_DIR, "preview.mp3")
                    with st.spinner("နမူနာ အသံထုတ်နေသည်..."):
                        tts_generate_file(preview_text, voice, p_path)
                        st.audio(p_path)

        with col_g2:
            if st.button("🚀 အသံဖိုင် အပြည့်အစုံ ဖန်တီးမည်", type="primary", use_container_width=True):
                if not gen_text.strip():
                    st.error("စာသားအရင် ရိုက်ထည့်ပေးပါ")
                else:
                    final_text = apply_pronunciation(gen_text, st.session_state.pron_dict)
                    out_gen_audio = os.path.join(WORK_DIR, f"tts_{uuid.uuid4().hex[:6]}.mp3")
                    with st.spinner("အသံဖိုင် ဖန်တီးနေပါသည်..."):
                        tts_generate_file(final_text, voice, out_gen_audio)
                        st.success("အသံဖိုင် ဖန်တီးပြီးပါပြီ!")
                        st.audio(out_gen_audio)
                        
                        audio_len = dur(out_gen_audio)
                        gen_srt = generate_proportional_srt(final_text, audio_len)

                        d_c1, d_c2 = st.columns(2)
                        with d_c1:
                            with open(out_gen_audio, "rb") as f:
                                st.download_button("⬇️ Download Audio (MP3)", f, file_name="Voiceover.mp3", mime="audio/mpeg", use_container_width=True)
                        with d_c2:
                            st.download_button("⬇️ Download Subtitle (SRT)", gen_srt, file_name="Voiceover.srt", mime="text/plain", use_container_width=True)

    # =========================================================================
    # TAB 2: Auto Transcript Studio
    # =========================================================================
    with tab_transcript:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">2</span><span>Video မှ Script နှင့် Voiceover အလိုအလျောက် ထုတ်ယူမည်</span></div>', unsafe_allow_html=True)
        st.caption("Video ဖိုင်ကို တင်လိုက်ရုံဖြင့် အသံကို နားထောင်ပြီး YouTube/Facebook အတွက် ခေါင်းစဉ် ၅ ခု၊ ဇာတ်လမ်း Script နှင့် မြန်မာ Voiceover အသစ် ထုတ်ပေးပါမည်။")

        trans_file = st.file_uploader("MP4 / WebM / MKV Video ဖိုင် တင်ပါ", type=["mp4", "webm", "mkv"], key="trans_uploader")
        
        c_t1, c_t2 = st.columns(2)
        with c_t1:
            trans_dur = st.selectbox("ဇာတ်လမ်း အရှည် (Duration)", ["1", "2", "3", "5"],
                                     format_func=lambda d: f"{d} မိနစ်စာ Script")
        with c_t2:
            trans_lang = st.selectbox("ဗီဒီယို မူရင်းဘာသာစကား", ["Auto", "English", "Korean", "Japanese", "Chinese", "Thai"])
            t_lang_code = None if trans_lang == "Auto" else {"English": "en", "Korean": "ko", "Japanese": "ja", "Chinese": "zh", "Thai": "th"}[trans_lang]

        if trans_file and st.button("✨ Auto Transcript & Voiceover စတင်ထုတ်မည်", type="primary", use_container_width=True):
            if not gemini_key or not groq_key:
                st.error("Sidebar တွင် Gemini API Key နှင့် Groq API Key ထည့်သွင်းပေးပါ")
                st.stop()

            run_id = uuid.uuid4().hex[:8]
            rd = os.path.join(WORK_DIR, run_id)
            os.makedirs(rd, exist_ok=True)
            vpath = os.path.join(rd, trans_file.name)
            with open(vpath, "wb") as f:
                f.write(trans_file.getbuffer())

            with st.status("Auto Transcript စနစ် လည်ပတ်နေပါသည်...", expanded=True) as status_box:
                # 1. Audio Extraction
                status_box.update(label="ဗီဒီယိုမှ အသံဖိုင် ခွဲထုတ်နေပါသည်...")
                wpath = os.path.join(rd, "extracted_audio.mp3")
                run(["ffmpeg", "-y", "-v", "error", "-i", vpath, "-ar", "16000", "-ac", "1", "-b:a", "32k", wpath])

                # 2. Groq Whisper Transcription
                status_box.update(label="Groq Whisper ဖြင့် အသံကို နားထောင်နေပါသည်...")
                segs = transcribe_audio_groq(wpath, groq_key, t_lang_code)
                raw_text = " ".join([s["text"] for s in segs])

                # 3. Gemini Script & Titles Generation
                status_box.update(label="Gemini မှ ဇာတ်လမ်းနှင့် ခေါင်းစဉ်များ ရေးသားနေပါသည်...")
                res_meta = gemini_generate_transcript(gemini_key, GEMINI_MODEL_DEFAULT, raw_text, trans_dur)
                script_body = res_meta.get("script", "")
                script_body_pron = apply_pronunciation(script_body, st.session_state.pron_dict)

                # 4. Generate Myanmar Voiceover
                status_box.update(label="မြန်မာအသံဖိုင် အသစ် ဖန်တီးနေပါသည်...")
                out_trans_audio = os.path.join(rd, "dubbed_voiceover.mp3")
                tts_generate_file(script_body_pron, voice, out_trans_audio)
                
                audio_dur = dur(out_trans_audio)
                srt_content = generate_proportional_srt(script_body, audio_dur)
                status_box.update(label="ပြီးမြောက်ပါပြီ!", state="complete")

            st.success("🎉 Auto Transcript နှင့် Voiceover အောင်မြင်စွာ ထုတ်ယူပြီးပါပြီ!")

            # Generated Titles Box
            st.subheader("📌 အကြံပြု ခေါင်းစဉ်များ (Viral Titles with Tags):")
            for t_title in res_meta.get("titles", []):
                st.code(t_title, language="text")

            # Script Area
            st.subheader("📝 ထွက်ရှိလာသော Script:")
            st.text_area("Script စာသား:", value=script_body, height=200)

            # Audio Player & Downloads
            st.subheader("🔊 ထွက်ရှိလာသော Voiceover အသံဖိုင်:")
            st.audio(out_trans_audio)

            d_tc1, d_tc2 = st.columns(2)
            with d_tc1:
                with open(out_trans_audio, "rb") as f:
                    st.download_button("⬇️ Download Voiceover (MP3)", f, file_name="Auto_Voiceover.mp3", mime="audio/mpeg", use_container_width=True)
            with d_tc2:
                st.download_button("⬇️ Download Subtitle (SRT)", srt_content, file_name="Auto_Subtitle.srt", mime="text/plain", use_container_width=True)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Spidy Dub Studio & Bo Gyi AI Studio — All-in-One Complete Edition

Features:
  1. 🕷️ Spidy Original Video Dubbing:
     - 6-step wizard (Upload -> Whisper -> Translate -> Review -> TTS -> Render)
     - ⚡ Auto Mode (One-click)
     - 🎞️ Recap Render (video slow/fast-mo narration sync)
     - ⚡ Speed-up (up to 2.0x sync)
     - 📝 Subtitle Burn-in directly onto Final Video
  2. 🎙️ Gemini TTS Generator & Voice Actors (From MyBest):
     - 20 Voice Actors (အောင်အောင်, ရဲရင့်, စုစု, etc.)
     - 21 Emotions & Tones
     - 17 Pitches & Styles
     - Custom Pronunciation Dictionary
     - Script Preview
  3. 📜 AI Script Writer & Auto Transcript:
     - Video -> Script (12 Styles, Duration Selection)
     - Viral Titles (5 Titles with Hashtags) & Social Description
     - Generate Voiceover from Script
  4. 🖼️ AI Thumbnail Maker:
     - 16:9, 9:16, 4:5 Thumbnails with custom colors and styles
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
.spidey-hero { text-align: center; padding: 16px 0 4px; }
.spidey-kicker { color: #8A93B8; font-size: .78rem; letter-spacing: 3px; font-weight: 700; }
.spidey-title {
    font-family: 'Bangers', 'Arial Black', sans-serif;
    font-size: 3.2rem; letter-spacing: 2px; color: #F03A3A;
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

# ---------------------------------------------------------- Constants from MyBest & Spidy
GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3"
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"

VOICES = [
  { 'id': 'Charon', 'name': 'အောင်အောင်', 'gender': 'Male', 'desc': 'သြဇာပါသော' },
  { 'id': 'Fenrir', 'name': 'ရဲရင့်', 'gender': 'Male', 'desc': 'ခွန်အားပါသော' },
  { 'id': 'Orus', 'name': 'မင်းခန့်', 'gender': 'Male', 'desc': 'တည်ငြိမ်သော' },
  { 'id': 'Enceladus', 'name': 'ဇေယျာ', 'gender': 'Male', 'desc': 'ရင့်ကျက်သော' },
  { 'id': 'Iapetus', 'name': 'ထက်မြတ်', 'gender': 'Male', 'desc': 'ယုံကြည်မှုရှိသော' },
  { 'id': 'Algenib', 'name': 'မျိုးမင်း', 'gender': 'Male', 'desc': 'ကြည်လင်သော' },
  { 'id': 'Rasalgethi', 'name': 'စည်သူ', 'gender': 'Male', 'desc': 'နွေးထွေးသော' },
  { 'id': 'Schedar', 'name': 'ကောင်းကင်', 'gender': 'Male', 'desc': 'အားတက်ဖွယ်ရာ' },
  { 'id': 'Alnilam', 'name': 'သီဟ', 'gender': 'Male', 'desc': 'ရှင်းလင်းပြတ်သားသော' },
  { 'id': 'Sadachbia', 'name': 'ဝေယံ', 'gender': 'Male', 'desc': 'ဖော်ရွေသော' },
  { 'id': 'Kore', 'name': 'စုစု', 'gender': 'Female', 'desc': 'ချိုသာသော' },
  { 'id': 'Aoede', 'name': 'သန္တာ', 'gender': 'Female', 'desc': 'နူးညံ့သော' },
  { 'id': 'Leda', 'name': 'လှိုင်', 'gender': 'Female', 'desc': 'တောက်ပသော' },
  { 'id': 'Callirrhoe', 'name': 'အေးအေး', 'gender': 'Female', 'desc': 'အေးချမ်းသော' },
  { 'id': 'Autonoe', 'name': 'မြမြ', 'gender': 'Female', 'desc': 'ရှင်းလင်းသော' },
  { 'id': 'Despina', 'name': 'နန်းဆု', 'gender': 'Female', 'desc': 'ချစ်စရာကောင်းသော' },
  { 'id': 'Erinome', 'name': 'ရွှေရည်', 'gender': 'Female', 'desc': 'ဖော်ရွေသော' },
  { 'id': 'Laomedeia', 'name': 'သီရိ', 'gender': 'Female', 'desc': 'တည်ငြိမ်သော' },
  { 'id': 'Achernar', 'name': 'မေမီ', 'gender': 'Female', 'desc': 'ကြည်လင်ပြတ်သားသော' },
  { 'id': 'Gacrux', 'name': 'နှင်းနှင်း', 'gender': 'Female', 'desc': 'လန်းဆန်းသော' },
  { 'id': 'my-MM-ThihaNeural', 'name': 'Thiha (Edge-TTS)', 'gender': 'Male', 'desc': 'သဘာဝကျသော' },
  { 'id': 'my-MM-NilarNeural', 'name': 'Nilar (Edge-TTS)', 'gender': 'Female', 'desc': 'သဘာဝကျသော' }
]

EMOTIONS = [
  { 'id': 'Neutral', 'label': 'ပုံမှန်', 'enLabel': 'Neutral', 'emoji': '😐' },
  { 'id': 'MovieRecap', 'label': 'Movie Recap (အမြန်)', 'enLabel': 'fast-paced and energetic movie recap', 'emoji': '🎬' },
  { 'id': 'Happy', 'label': 'ပျော်ရွှင်သော', 'enLabel': 'Happy', 'emoji': '😊' },
  { 'id': 'Sad', 'label': 'ဝမ်းနည်းသော', 'enLabel': 'Sad', 'emoji': '😢' },
  { 'id': 'Angry', 'label': 'ဒေါသထွက်သော', 'enLabel': 'Angry', 'emoji': '😠' },
  { 'id': 'Calm', 'label': 'တည်ငြိမ်သော', 'enLabel': 'Calm', 'emoji': '😌' },
  { 'id': 'Energetic', 'label': 'တက်ကြွသော', 'enLabel': 'Energetic', 'emoji': '⚡' },
  { 'id': 'Whisper', 'label': 'တိုးတိုးပြော', 'enLabel': 'Whispering', 'emoji': '🤫' },
  { 'id': 'Storytelling', 'label': 'ပုံပြင်ပြော', 'enLabel': 'Storytelling', 'emoji': '📖' },
  { 'id': 'Professional', 'label': 'လုပ်ငန်းသုံး', 'enLabel': 'Professional', 'emoji': '👔' },
  { 'id': 'Casual', 'label': 'ပေါ့ပေါ့ပါးပါး', 'enLabel': 'Casual', 'emoji': '☕' },
  { 'id': 'Fearful', 'label': 'ကြောက်ရွံ့သော', 'enLabel': 'Fearful', 'emoji': '😨' },
  { 'id': 'Surprised', 'label': 'အံ့သြသော', 'enLabel': 'Surprised', 'emoji': '😲' },
  { 'id': 'Excited', 'label': 'စိတ်လှုပ်ရှားသော', 'enLabel': 'Excited', 'emoji': '🤩' },
  { 'id': 'Romantic', 'label': 'ချစ်စရာကောင်းသော', 'enLabel': 'Romantic', 'emoji': '🥰' },
  { 'id': 'Sarcastic', 'label': 'ခနဲ့တဲ့တဲ့', 'enLabel': 'Sarcastic', 'emoji': '😏' },
  { 'id': 'Serious', 'label': 'လေးနက်သော', 'enLabel': 'Serious', 'emoji': '🧐' },
  { 'id': 'Confident', 'label': 'ယုံကြည်မှုရှိသော', 'enLabel': 'Confident', 'emoji': '😎' },
  { 'id': 'Shy', 'label': 'ရှက်တတ်သော', 'enLabel': 'Shy', 'emoji': '😳' },
  { 'id': 'Hopeful', 'label': 'မျှော်လင့်ချက်ရှိသော', 'enLabel': 'Hopeful', 'emoji': '🤞' },
  { 'id': 'Tired', 'label': 'ပင်ပန်းနေသော', 'enLabel': 'Tired', 'emoji': '😫' }
]

PITCHES = [
  { 'id': 'default', 'label': 'ပုံမှန် (Default)', 'prompt': '', 'emoji': '🎵' },
  { 'id': 'movie_recap', 'label': 'Energetic Movie Recap', 'prompt': 'an energetic, fast-paced, and engaging movie recap pitch', 'emoji': '🎬' },
  { 'id': 'sci_fi', 'label': 'Epic Sci-Fi Narrator', 'prompt': 'an epic, futuristic, and dramatic sci-fi narrator pitch', 'emoji': '🌌' },
  { 'id': 'sarcastic', 'label': 'Sarcastic & Witty', 'prompt': 'a sarcastic, witty, and clever tone', 'emoji': '😏' },
  { 'id': 'anime', 'label': 'Anime Protagonist', 'prompt': 'an intense, passionate, and highly dramatic anime protagonist pitch', 'emoji': '⚔️' },
  { 'id': 'vlogger', 'label': 'Friendly Vlogger', 'prompt': 'a cheerful, casual, and friendly YouTube vlogger tone', 'emoji': '📹' },
  { 'id': 'tech', 'label': 'Tech Reviewer', 'prompt': 'a clear, analytical, and modern tech reviewer pitch', 'emoji': '📱' },
  { 'id': 'asmr', 'label': 'Whispering ASMR', 'prompt': 'a soft, close-mic whispering ASMR pitch', 'emoji': '🎙️' },
  { 'id': 'comedy', 'label': 'Comedy & Playful', 'prompt': 'a playful, funny, and comedic tone', 'emoji': '😂' },
  { 'id': 'action', 'label': 'Action & Thriller', 'prompt': 'a tense, fast, and gripping action thriller pitch', 'emoji': '💥' },
  { 'id': 'nature', 'label': 'Documentary Nature', 'prompt': 'a calm, majestic, and soothing nature documentary narrator pitch', 'emoji': '🌿' },
  { 'id': 'sad', 'label': 'Emotional & Sad', 'prompt': 'a highly emotional, melancholy, and sad tone', 'emoji': '😢' },
  { 'id': 'news', 'label': 'News Anchor', 'prompt': 'a professional, authoritative, and clear news anchor pitch', 'emoji': '📰' },
  { 'id': 'storyteller', 'label': 'Storyteller', 'prompt': 'an expressive, engaging, and immersive storytelling pitch', 'emoji': '📖' },
  { 'id': 'professional', 'label': 'Calm & Professional', 'prompt': 'a calm, steady, and highly professional tone', 'emoji': '👔' },
  { 'id': 'horror', 'label': 'Horror & Suspense', 'prompt': 'a creepy, suspenseful, and dark horror pitch', 'emoji': '👻' },
  { 'id': 'romantic', 'label': 'Romantic & Soft', 'prompt': 'a tender, romantic, and soft pitch', 'emoji': '💕' }
]

SCRIPT_STYLES = [
  { 'id': '1', 'title': 'Movie Recap', 'prompt': 'Movie Recap: Summarize the events from start to finish as an engaging story.' },
  { 'id': '2', 'title': 'Cinematic Documentary', 'prompt': 'Cinematic Documentary: Provide a professional, cinematic, and dramatic documentary narration.' },
  { 'id': '3', 'title': 'Storytelling', 'prompt': 'Storytelling: Tell the story naturally and easily as if speaking to a friend.' },
  { 'id': '4', 'title': 'Viral Short', 'prompt': 'Viral Short: Start with a strong hook, keep it fast-paced and highly engaging for short-form content.' },
  { 'id': '5', 'title': 'Mystery / Investigation', 'prompt': 'Mystery / Investigation: Reveal clues step-by-step, build suspense, and provide a final reveal.' },
  { 'id': '6', 'title': 'Horror / Dark Story', 'prompt': 'Horror / Dark Story: Build a scary atmosphere, suspense, and tension using dark storytelling.' },
  { 'id': '7', 'title': 'News / Report', 'prompt': 'News / Report: Fact-based, accurate, and professional like a news report.' },
  { 'id': '8', 'title': 'Explainer / Educational', 'prompt': 'Explainer / Educational: Explain the "what, why, and how" clearly and easily.' },
  { 'id': '9', 'title': 'Emotional Story', 'prompt': 'Emotional Story: Focus on emotions like sadness, joy, surprise, or inspiration.' },
  { 'id': '10', 'title': 'Dramatic / Epic', 'prompt': 'Dramatic / Epic: Use powerful narration, dramatic build-up, and high-impact words like a movie trailer.' }
]

_DEFAULT_PRON_DICT = [
    {"word": "AI", "replace": "အေအိုင်"},
    {"word": "Crypto", "replace": "ခရစ်ပတို"},
    {"word": "Delight", "replace": "ဒီလိုက်"},
    {"word": "Recap", "replace": "ရီကပ်"}
]

# ------------------------------------------------------------------ Helpers
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

# ------------------------------------------------------- Universal TTS (Edge + Gemini TTS)
async def _edge_save(text, voice, path):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(path)

def _gemini_tts_save(text, voice_id, emotion_id, pitch_id, api_key, path):
    em = next((e['enLabel'] for e in EMOTIONS if e['id'] == emotion_id), "Neutral")
    pt = next((p['prompt'] for p in PITCHES if p['id'] == pitch_id), "")
    tone_str = f"tone: {em}, pitch: {pt}".strip(", ")
    prompt = f"Read the following text in natural spoken Burmese. {tone_str}\n\nText:\n{text}"

    endpoint = "gemini-2.5-flash-preview-tts"
    url = f"{GEMINI_BASE}{endpoint}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice_id}}}
        }
    }
    r = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=90)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini TTS Error: {r.text[:200]}")
    b64_audio = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    raw_pcm = base64.b64decode(b64_audio)
    
    # Save as WAV with RIFF header
    wav_header = bytearray(44)
    pcm_len = len(raw_pcm)
    wav_header[0:4] = b'RIFF'
    wav_header[4:8] = (36 + pcm_len).to_bytes(4, 'little')
    wav_header[8:12] = b'WAVE'
    wav_header[12:16] = b'fmt '
    wav_header[16:20] = (16).to_bytes(4, 'little')
    wav_header[20:22] = (1).to_bytes(2, 'little')
    wav_header[22:24] = (1).to_bytes(2, 'little')
    wav_header[24:28] = (24000).to_bytes(4, 'little')
    wav_header[28:32] = (24000 * 2).to_bytes(4, 'little')
    wav_header[32:34] = (2).to_bytes(2, 'little')
    wav_header[34:36] = (16).to_bytes(2, 'little')
    wav_header[36:40] = b'data'
    wav_header[40:44] = (pcm_len).to_bytes(4, 'little')

    with open(path, "wb") as f:
        f.write(wav_header + raw_pcm)

def generate_any_tts(text, voice_id, emotion_id, pitch_id, api_key, out_path):
    if voice_id.startswith("my-MM-"):
        asyncio.run(_edge_save(text, voice_id, out_path))
    else:
        _gemini_tts_save(text, voice_id, emotion_id, pitch_id, api_key, out_path)
    return out_path

# ------------------------------------------------------- Gemini Calls
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
        raise RuntimeError(f"Gemini error: {r.text[:200]}")
    txt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    if json_mode:
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt)
        return json.loads(txt.strip())
    return txt

def gemini_translate(api_key, segments, model_id):
    sys_prompt = "Translate video subtitle lines into natural SPOKEN Burmese Unicode script. Return JSON array of objects with keys 'id' and 'text'."
    items = [{"id": i, "text": s["text"]} for i, s in enumerate(segments)]
    out = {}
    BATCH = 25
    for i in range(0, len(items), BATCH):
        batch = items[i:i+BATCH]
        try:
            res = _gemini_call(api_key, model_id, sys_prompt, json.dumps(batch, ensure_ascii=False))
            for row in res:
                if isinstance(row, dict) and "id" in row and "text" in row:
                    out[int(row["id"])] = str(row["text"]).strip()
        except Exception:
            pass
    return [{"start": s["start"], "end": s["end"], "src": s["text"], "text": out.get(i, s["text"])} for i, s in enumerate(segments)]

# ------------------------------------------------------- STT & Render
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

def render_recap_video(video_path, natural, total_duration, work_dir, out_mp4):
    n = len(natural)
    pieces = []
    if natural[0]["start"] > 0.05:
        pieces.append((0.0, natural[0]["start"], natural[0]["start"]))
    for i, sg in enumerate(natural):
        b = natural[i + 1]["start"] if i + 1 < n else total_duration
        b = max(b, sg["end"])
        gap = max(0.0, b - sg["end"])
        pieces.append((sg["start"], b, sg["dur"] + gap))

    fparts, vlabels = [], []
    for j, (a, b, target) in enumerate(pieces):
        p_dur = b - a
        factor = min(max(target / p_dur if p_dur > 0.05 else 1.0, 0.05), 20.0)
        fparts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},settb=AVTB,setpts=(PTS-STARTPTS)*{factor:.4f}[v{j}]")
        vlabels.append(f"[v{j}]")
    fcomplex = ";".join(fparts) + ";" + "".join(vlabels) + f"concat=n={len(pieces)}:v=1:a=0,fps=30[vout]"

    lst = os.path.join(work_dir, "recap_audio.txt")
    with open(lst, "w") as fh:
        if natural[0]["start"] > 0.05:
            gf = os.path.join(work_dir, f"_lead_gap.mp3")
            silence(gf, natural[0]["start"])
            fh.write(f"file '{os.path.abspath(gf)}'\n")
        for i, sg in enumerate(natural):
            fh.write(f"file '{os.path.abspath(sg['mp3'])}'\n")
            b = natural[i + 1]["start"] if i + 1 < n else total_duration
            gap = max(0.0, b - sg["end"])
            if gap > 0.02:
                gf = os.path.join(work_dir, f"_rgap{round(gap, 2)}.mp3")
                if not os.path.exists(gf):
                    silence(gf, gap)
                fh.write(f"file '{os.path.abspath(gf)}'\n")

    run(["ffmpeg", "-y", "-v", "error", "-i", video_path, "-f", "concat", "-safe", "0", "-i", lst,
         "-filter_complex", fcomplex, "-map", "[vout]", "-map", "1:a:0",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", "-shortest", out_mp4])

    timeline, cum = [], natural[0]["start"] if natural[0]["start"] > 0.05 else 0.0
    for i, sg in enumerate(natural):
        b = natural[i + 1]["start"] if i + 1 < n else total_duration
        target = sg["dur"] + max(0.0, b - sg["end"])
        timeline.append({"start": cum, "end": cum + sg["dur"], "text": sg["text"]})
        cum += target
    return out_mp4, timeline

def speedup_video(video_in, factor, out_mp4):
    if abs(factor - 1.0) < 1e-6:
        shutil.copyfile(video_in, out_mp4)
        return out_mp4
    run(["ffmpeg", "-y", "-v", "error", "-i", video_in,
         "-vf", f"setpts=PTS/{factor:.4f}", "-af", f"atempo={factor:.4f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", out_mp4])
    return out_mp4

def burn_subtitles_to_video(video_in, srt_path, out_mp4):
    escaped_srt = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")
    sub_filter = (
        f"subtitles='{escaped_srt}':force_style='FontName=Noto Sans Myanmar,FontSize=16,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=25'"
    )
    run(["ffmpeg", "-y", "-v", "error", "-i", video_in, "-vf", sub_filter,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "copy",
         "-movflags", "+faststart", out_mp4])
    return out_mp4

# ------------------------------------------------------- Main Application UI
def main():
    st.set_page_config(page_title="Spidy Dub & Bo Gyi AI Studio", page_icon="🕷️", layout="wide")
    st.markdown(_SPIDEY_CSS, unsafe_allow_html=True)

    if "pron_dict" not in st.session_state:
        st.session_state.pron_dict = _DEFAULT_PRON_DICT.copy()

    # Sidebar
    with st.sidebar:
        st.markdown("### 🕷️ Control Center")
        gemini_key = st.text_input("Gemini API Key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
        groq_key = st.text_input("Groq API Key", value=os.environ.get("GROQ_API_KEY", ""), type="password")

        st.divider()
        st.markdown("#### 🗣️ Voice Actor & Emotion")
        selected_voice = st.selectbox("အသံသရုပ်ဆောင်", [v['id'] for v in VOICES],
                                      format_func=lambda vid: f"{next(v['name'] for v in VOICES if v['id'] == vid)} ({next(v['desc'] for v in VOICES if v['id'] == vid)})")
        selected_emotion = st.selectbox("ခံစားချက် (Emotion)", [e['id'] for e in EMOTIONS],
                                        format_func=lambda eid: f"{next(e['emoji'] for e in EMOTIONS if e['id'] == eid)} {next(e['label'] for e in EMOTIONS if e['id'] == eid)}")
        selected_pitch = st.selectbox("အနိမ့်အမြင့် (Pitch)", [p['id'] for p in PITCHES],
                                      format_func=lambda pid: f"{next(p['emoji'] for p in PITCHES if p['id'] == pid)} {next(p['label'] for p in PITCHES if p['id'] == pid)}")

        st.divider()
        st.markdown("#### ⚡ Video Render Options")
        speedup = st.slider("⚡ Speed တင် (1.0x - 2.0x)", 1.0, 2.0, 1.0, 0.05)
        burn_subs = st.checkbox("📝 Video Final တွင် Subtitle ထိုးမည်", value=True)

        st.divider()
        with st.expander("📖 Custom Pronunciation Dictionary"):
            pw = st.text_input("Word (e.g. AI)", key="pw")
            pr = st.text_input("Replace (e.g. အေအိုင်)", key="pr")
            if st.button("➕ ထည့်သွင်းမည်"):
                if pw and pr:
                    st.session_state.pron_dict.append({"word": pw, "replace": pr})
                    st.success("ထည့်ပြီးပါပြီ")
            st.json(st.session_state.pron_dict)

    st.markdown(
        '<div class="spidey-hero">'
        '<div class="spidey-kicker">🕸️ ALL-IN-ONE VIDEO DUB & CREATOR STUDIO 🕸️</div>'
        '<div class="spidey-title">Spidy Dub Studio</div>'
        '<div class="spidey-sub">Spidy Dubbing • Voice Generator • Auto Transcript • Script Writer • Thumbnail 🕷️</div>'
        '</div>', unsafe_allow_html=True
    )

    tabs = st.tabs([
        "🎬 Spidy Video Dubbing",
        "🔊 အသံဖန်တီးမည် (Generator)",
        "✨ Auto Transcript Studio",
        "📝 AI Script Writer",
        "🖼️ Thumbnail Maker"
    ])

    # =========================================================================
    # TAB 1: SPIDY ORIGINAL VIDEO DUBBING
    # =========================================================================
    with tabs[0]:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">1</span><span>ဗီဒီယို Dubbing စနစ်</span></div>', unsafe_allow_html=True)
        v_file = st.file_uploader("ဗီဒီယိုဖိုင် တင်ပါ (MP4/WebM)", type=["mp4", "webm", "mov"], key="spidy_vup")
        
        c1, c2 = st.columns(2)
        with c1:
            dub_lang = st.selectbox("မူရင်းဘာသာစကား", ["Auto", "English", "Korean", "Japanese", "Chinese", "Thai"])
            l_code = None if dub_lang == "Auto" else {"English": "en", "Korean": "ko", "Japanese": "ja", "Chinese": "zh", "Thai": "th"}[dub_lang]
        with c2:
            recap_mode = st.checkbox("🎞️ Recap Render (Narration အရှည်အတိုင်း Video ချိန်ညှိခြင်း)", value=True)

        if v_file and st.button("🚀 ဗီဒီယို အပြည့်အစုံ Dubbing စတင်မည်", type="primary", use_container_width=True):
            if not gemini_key or not groq_key:
                st.error("Sidebar တွင် Gemini Key နှင့် Groq Key ထည့်သွင်းပါ")
                st.stop()

            run_id = uuid.uuid4().hex[:8]
            rd = os.path.join(WORK_DIR, run_id)
            os.makedirs(rd, exist_ok=True)
            vpath = os.path.join(rd, v_file.name)
            with open(vpath, "wb") as f:
                f.write(v_file.getbuffer())

            with st.status("Spidy Pipeline စတင်နေပါသည်...", expanded=True) as sbox:
                sbox.update(label="1/5: ဗီဒီယိုမှ Audio ခွဲထုတ်နေသည်...")
                wpath = os.path.join(rd, "audio.mp3")
                run(["ffmpeg", "-y", "-v", "error", "-i", vpath, "-ar", "16000", "-ac", "1", "-b:a", "32k", wpath])
                total_d = dur(vpath)

                sbox.update(label="2/5: Groq Whisper ဖြင့် စာသားထုတ်နေသည်...")
                segs = transcribe_audio_groq(wpath, groq_key, l_code)

                sbox.update(label="3/5: Gemini ဖြင့် သဘာဝကျသော မြန်မာစကားပြော ပြန်ဆိုနေသည်...")
                trans = gemini_translate(gemini_key, segs, GEMINI_MODEL_DEFAULT)

                sbox.update(label="4/5: ရွေးချယ်ထားသော Voice Actor ဖြင့် မြန်မာအသံထုတ်နေသည်...")
                natural = []
                for s in trans:
                    text_p = apply_pronunciation(s["text"], st.session_state.pron_dict)
                    seg_out = os.path.join(rd, f"seg_{uuid.uuid4().hex[:6]}.wav")
                    generate_any_tts(text_p, selected_voice, selected_emotion, selected_pitch, gemini_key, seg_out)
                    natural.append({"start": s["start"], "end": s["end"], "text": text_p, "mp3": seg_out, "dur": dur(seg_out)})

                sbox.update(label="5/5: Video နှင့် Audio ကို ချိန်ညှိ ပေါင်းစပ်နေသည်...")
                work_rc = os.path.join(rd, "rc")
                raw_mp4 = os.path.join(work_rc, "recap.mp4")
                _, timeline = render_recap_video(vpath, natural, total_d, work_rc, raw_mp4)

                stage_mp4 = raw_mp4
                subs_final = timeline

                # Speed-up (2.0x)
                if speedup > 1.0:
                    sbox.update(label=f"အမြန်နှုန်းကို {speedup}x သို့ တင်နေသည်...")
                    sp_mp4 = os.path.join(rd, "sped.mp4")
                    speedup_video(stage_mp4, speedup, sp_mp4)
                    stage_mp4 = sp_mp4
                    subs_final = [{"start": s["start"]/speedup, "end": s["end"]/speedup, "text": s["text"]} for s in subs_final]

                # Subtitle Burn-in
                if burn_subs and subs_final:
                    sbox.update(label="ဗီဒီယိုထဲသို့ မြန်မာ Subtitle စာတန်းထိုးနေသည်...")
                    srt_p = os.path.join(rd, "sub.srt")
                    with open(srt_p, "w", encoding="utf-8") as f:
                        f.write(segments_to_srt(subs_final))
                    bn_mp4 = os.path.join(rd, "burned.mp4")
                    try:
                        burn_subtitles_to_video(stage_mp4, srt_p, bn_mp4)
                        stage_mp4 = bn_mp4
                    except Exception as e:
                        st.warning(f"Burn-in warning: {e}")

                final_mp4 = os.path.join(rd, "final_dubbed.mp4")
                shutil.copyfile(stage_mp4, final_mp4)
                sbox.update(label="ပြီးမြောက်ပါပြီ!", state="complete")

            st.success("✅ Dubbing ပြီးမြောက်ပါပြီ!")
            st.video(final_mp4)
            d1, d2 = st.columns(2)
            with d1:
                with open(final_mp4, "rb") as f:
                    st.download_button("⬇️ Download Dubbed Video", f, file_name="Spidy_Dubbed.mp4", mime="video/mp4", use_container_width=True)
            with d2:
                st.download_button("⬇️ Download Subtitle (SRT)", segments_to_srt(subs_final), file_name="Spidy_Sub.srt", mime="text/plain", use_container_width=True)

    # =========================================================================
    # TAB 2: အသံဖန်တီးမည် (MYBEST TTS GENERATOR)
    # =========================================================================
    with tabs[1]:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">2</span><span>အသံဖန်တီးမည် (TTS Generator)</span></div>', unsafe_allow_html=True)
        txt_input = st.text_area("အသံဖန်တီးလိုသော စာသားကို ရိုက်ထည့်ပါ:", height=250, placeholder="မင်္ဂလာပါ... အသံဖတ်လိုသော စာသားများကို ဒီမှာရိုက်ထည့်ပါ...")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 အစမ်းနားထောင်မည် (Preview)", use_container_width=True):
                if not txt_input.strip():
                    st.warning("စာသားအရင် ရိုက်ထည့်ပါ")
                else:
                    snippet = apply_pronunciation(txt_input[:120], st.session_state.pron_dict)
                    p_out = os.path.join(WORK_DIR, "preview.wav")
                    with st.spinner("အစမ်းထုတ်လုပ်နေသည်..."):
                        generate_any_tts(snippet, selected_voice, selected_emotion, selected_pitch, gemini_key, p_out)
                        st.audio(p_out)

        with c2:
            if st.button("🚀 အသံဖိုင် အပြည့်အစုံ ဖန်တီးမည်", type="primary", use_container_width=True):
                if not txt_input.strip():
                    st.error("စာသားအရင် ရိုက်ထည့်ပါ")
                else:
                    final_t = apply_pronunciation(txt_input, st.session_state.pron_dict)
                    full_out = os.path.join(WORK_DIR, f"tts_{uuid.uuid4().hex[:6]}.wav")
                    with st.spinner("Voice Actor ဖြင့် အသံဖန်တီးနေပါသည်..."):
                        generate_any_tts(final_t, selected_voice, selected_emotion, selected_pitch, gemini_key, full_out)
                        st.success("ဖန်တီးပြီးပါပြီ!")
                        st.audio(full_out)
                        
                        a_dur = dur(full_out)
                        gen_srt = generate_proportional_srt(final_t, a_dur)
                        
                        dc1, dc2 = st.columns(2)
                        with dc1:
                            with open(full_out, "rb") as f:
                                st.download_button("⬇️ Download Audio (WAV)", f, file_name="Voiceover.wav", mime="audio/wav", use_container_width=True)
                        with dc2:
                            st.download_button("⬇️ Download SRT Subtitle", gen_srt, file_name="Voiceover.srt", mime="text/plain", use_container_width=True)

    # =========================================================================
    # TAB 3: AUTO TRANSCRIPT STUDIO
    # =========================================================================
    with tabs[2]:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">3</span><span>Auto Transcript Studio</span></div>', unsafe_allow_html=True)
        t_file = st.file_uploader("ဗီဒီယို တင်ပါ", type=["mp4", "webm", "mkv"], key="auto_t_up")
        
        c1, c2 = st.columns(2)
        with c1:
            t_dur = st.selectbox("Script အရှည် (Duration)", ["1", "2", "3", "5"], format_func=lambda d: f"{d} မိနစ်စာ")
        with c2:
            t_lang = st.selectbox("ဗီဒီယို ဘာသာစကား", ["Auto", "English", "Korean", "Japanese", "Chinese", "Thai"], key="at_lang")
            t_lcode = None if t_lang == "Auto" else {"English": "en", "Korean": "ko", "Japanese": "ja", "Chinese": "zh", "Thai": "th"}[t_lang]

        if t_file and st.button("✨ Script နှင့် Voiceover အလိုအလျောက် ထုတ်ယူမည်", type="primary", use_container_width=True):
            if not gemini_key or not groq_key:
                st.error("Gemini Key နှင့် Groq Key ထည့်သွင်းပါ")
                st.stop()

            run_id = uuid.uuid4().hex[:8]
            rd = os.path.join(WORK_DIR, run_id)
            os.makedirs(rd, exist_ok=True)
            vpath = os.path.join(rd, t_file.name)
            with open(vpath, "wb") as f:
                f.write(t_file.getbuffer())

            with st.status("Auto Transcript စနစ် လည်ပတ်နေသည်...", expanded=True) as sbox:
                sbox.update(label="အသံ ခွဲထုတ်နေသည်...")
                wpath = os.path.join(rd, "audio.mp3")
                run(["ffmpeg", "-y", "-v", "error", "-i", vpath, "-ar", "16000", "-ac", "1", "-b:a", "32k", wpath])

                sbox.update(label="Groq Whisper ဖြင့် နားထောင်နေသည်...")
                segs = transcribe_audio_groq(wpath, groq_key, t_lcode)
                raw_text = " ".join([s["text"] for s in segs])

                sbox.update(label="Gemini ဖြင့် ဇာတ်လမ်းနှင့် ခေါင်းစဉ်များ ဖန်တီးနေသည်...")
                prompt = (
                    f"Write an engaging storytelling recap script in spoken Burmese ({t_dur} min length). "
                    "Also generate 5 viral clickbait Burmese titles ending with 4 hashtags. Return JSON with 'titles' and 'script'."
                )
                res_meta = _gemini_call(gemini_key, GEMINI_MODEL_DEFAULT, prompt, raw_text[:12000], json_mode=True)
                script_txt = res_meta.get("script", "")
                script_pron = apply_pronunciation(script_txt, st.session_state.pron_dict)

                sbox.update(label="Voice Actor ဖြင့် အသံဖန်တီးနေသည်...")
                out_vo = os.path.join(rd, "auto_vo.wav")
                generate_any_tts(script_pron, selected_voice, selected_emotion, selected_pitch, gemini_key, out_vo)
                sbox.update(label="ပြီးမြောက်ပါပြီ!", state="complete")

            st.success("🎉 အောင်မြင်စွာ ထုတ်ယူပြီးပါပြီ!")
            st.subheader("📌 အကြံပြု ခေါင်းစဉ်များ (Viral Titles):")
            for tit in res_meta.get("titles", []):
                st.code(tit, language="text")

            st.subheader("📝 ထွက်ရှိလာသော Script:")
            st.text_area("Script", value=script_txt, height=200)

            st.subheader("🔊 ထွက်ရှိလာသော Voiceover အသံဖိုင်:")
            st.audio(out_vo)
            
            with open(out_vo, "rb") as f:
                st.download_button("⬇️ Download Voiceover (WAV)", f, file_name="Auto_Voiceover.wav", mime="audio/wav")

    # =========================================================================
    # TAB 4: AI SCRIPT WRITER
    # =========================================================================
    with tabs[3]:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">4</span><span>AI Script Writer (10 Styles)</span></div>', unsafe_allow_html=True)
        sw_file = st.file_uploader("ဗီဒီယို တင်ပါ", type=["mp4", "webm"], key="sw_up")
        sw_style = st.selectbox("Script Style ရွေးချယ်ပါ", [s['id'] for s in SCRIPT_STYLES],
                                format_func=lambda sid: next(s['title'] for s in SCRIPT_STYLES if s['id'] == sid))

        if sw_file and st.button("✍️ Script ရေးသားမည်", type="primary", use_container_width=True):
            if not gemini_key or not groq_key:
                st.error("API Keys များ ထည့်သွင်းပါ")
                st.stop()

            run_id = uuid.uuid4().hex[:8]
            rd = os.path.join(WORK_DIR, run_id)
            os.makedirs(rd, exist_ok=True)
            vpath = os.path.join(rd, sw_file.name)
            with open(vpath, "wb") as f:
                f.write(sw_file.getbuffer())

            with st.status("Script ရေးသားနေသည်...", expanded=True) as sbox:
                wpath = os.path.join(rd, "audio.mp3")
                run(["ffmpeg", "-y", "-v", "error", "-i", vpath, "-ar", "16000", "-ac", "1", "-b:a", "32k", wpath])
                segs = transcribe_audio_groq(wpath, groq_key)
                raw_text = " ".join([s["text"] for s in segs])

                chosen_style = next(s['prompt'] for s in SCRIPT_STYLES if s['id'] == sw_style)
                prompt = (
                    f"You are an expert scriptwriter. Style: {chosen_style}. "
                    "Write an engaging Burmese spoken script. Start with a strong 5-sec hook. "
                    "Also generate 5 titles and a social media description caption. Return JSON with 'titles', 'script', 'description'."
                )
                sw_res = _gemini_call(gemini_key, GEMINI_MODEL_DEFAULT, prompt, raw_text[:12000], json_mode=True)
                sbox.update(label="ပြီးပါပြီ!", state="complete")

            st.subheader("🔥 ဆွဲဆောင်မှုရှိသော Titles:")
            for tit in sw_res.get("titles", []):
                st.code(tit, language="text")

            st.subheader("📝 Script ရလဒ်:")
            st.text_area("Generated Script", value=sw_res.get("script", ""), height=250)

            st.subheader("💬 Social Media Caption:")
            st.code(sw_res.get("description", ""), language="text")

    # =========================================================================
    # TAB 5: AI THUMBNAIL MAKER
    # =========================================================================
    with tabs[4]:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">5</span><span>AI Thumbnail Maker</span></div>', unsafe_allow_html=True)
        th_ctx = st.text_area("Thumbnail အကြောင်းအရာ (Topic)", placeholder="ဥပမာ - ရန်သူမသိအောင် တိုက်ခိုက်နိုင်တဲ့ B-2 Spirit လေယာဉ်...")
        th_tit = st.text_input("ပုံပေါ်တွင် ရေးမည့်စာသား (Title Typography - Optional)")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            th_ratio = st.selectbox("အရွယ်အစား", ["16:9", "9:16", "4:5"])
        with c2:
            th_color = st.selectbox("စာသားအရောင်", ["Neon Cyan & Bright Yellow", "Pure White with Heavy Shadow", "Blood Red & White", "Gold & Luxury Black"])
        with c3:
            th_style = st.selectbox("အနုပညာစတိုင်", ["Epic, dramatic, and cinematic with high contrast", "Cyberpunk, neon lights", "Anime style, dynamic action", "Dark, mysterious, horror"])

        if st.button("🎨 Thumbnail ဖန်တီးမည်", type="primary", use_container_width=True):
            if not gemini_key:
                st.error("Gemini API Key ထည့်ပါ")
            elif not th_ctx.strip():
                st.warning("အကြောင်းအရာ ရိုက်ထည့်ပါ")
            else:
                with st.spinner("AI မှ Thumbnail ဖန်တီးနေပါသည်..."):
                    try:
                        p_txt = f"Create an epic clickbait YouTube thumbnail in {th_ratio} format. Subject: {th_ctx}. Style: {th_style}. "
                        if th_tit.strip():
                            p_txt += f"Typography: '{th_tit}' in {th_color}."
                        url = f"{GEMINI_BASE}gemini-2.5-flash-image-preview:generateContent?key={gemini_key}"
                        body = {"contents": [{"parts": [{"text": p_txt}]}], "generationConfig": {"responseModalities": ["IMAGE"]}}
                        r = requests.post(url, headers={"Content-Type": "application/json"}, json=body, timeout=120)
                        if r.status_code == 200:
                            b64_im = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                            img_b = base64.b64decode(b64_im)
                            st.image(img_b, caption="Generated Thumbnail", use_container_width=True)
                            st.download_button("⬇️ Download Image", img_b, file_name="Thumbnail.jpg", mime="image/jpeg")
                        else:
                            st.error(f"Error: {r.text[:200]}")
                    except Exception as e:
                        st.error(f"Thumbnail error: {e}")

if __name__ == "__main__":
    main()

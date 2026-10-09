#!/usr/bin/env python3
"""Spidy Dub Studio — All-in-One Video Dubbing & Creator Studio
(Dubbing + Title/Tags + Caption + Pronunciation Dict + Subtitle Burn-in + Speed 2.0x + Thumbnail Maker)
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

# ---------------------------------------------------------- 🕷️ UI CSS
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

def parse_ts(s):
    s = s.strip().replace(",", ".")
    parts = s.split(":")
    if len(parts) == 3:
        h, m, sec = parts
        return int(h) * 3600 + int(m) * 60 + float(sec)
    m, sec = parts
    return int(m) * 60 + float(sec)

def silence(path, seconds, sr=24000):
    run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi",
         "-i", "anullsrc=r=24000:cl=mono", "-t", f"{seconds:.3f}",
         "-ar", str(sr), path])

def apply_pronunciation(text, dict_list):
    """Pronunciation Dictionary အတိုင်း အင်္ဂလိပ်စာလုံးများကို မြန်မာအသံထွက်ပြောင်းခြင်း"""
    res = text
    for item in dict_list:
        w, r = item.get("word", "").strip(), item.get("replace", "").strip()
        if w and r:
            res = re.sub(re.escape(w), r, res, flags=re.IGNORECASE)
    return res

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

def gemini_translate(api_key, segments, model_id):
    sys_prompt = (
        "You translate video subtitle lines for Myanmar voiceover dubbing. "
        "Translate each line into natural SPOKEN Burmese (Myanmar). "
        "Write ONLY in Myanmar Unicode script. "
        "Return ONLY a JSON array of objects with keys 'id' and 'text'."
    )
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

def generate_social_assets(api_key, model_id, script_text):
    """ခေါင်းစဉ် ၅ ခု၊ Tags နှင့် Social Media Description ရေးပေးခြင်း"""
    sys_prompt = (
        "You are an expert viral content creator. Based on the provided Burmese video script, "
        "generate:\n"
        "1. Exactly 5 highly engaging, clickbaity YouTube/Facebook titles in Burmese (each title MUST end with 4 relevant hashtags).\n"
        "2. A compelling, engaging social media description (caption) with emojis in Burmese.\n"
        "Return ONLY a JSON object with keys 'titles' (list of strings) and 'description' (string)."
    )
    try:
        return _gemini_call(api_key, model_id, sys_prompt, script_text[:8000], json_mode=True)
    except Exception:
        return {"titles": [], "description": ""}

# ------------------------------------------------------- STT (Groq)
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

# ------------------------------------------------------- TTS & FFmpeg
async def _edge_save(text, voice, path):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(path)

def tts_segment(text, voice):
    key = hashlib.sha1(f"edge:{voice}:{text}".encode("utf-8")).hexdigest()[:16]
    out = os.path.join(CACHE_TTS, f"{key}.mp3")
    if os.path.isfile(out) and os.path.getsize(out) > 1000:
        return out
    try:
        asyncio.run(_edge_save(text, voice, out))
        return out
    except Exception:
        return None

def tts_natural(segments, voice, pron_dict):
    out = []
    for s in segments:
        text = apply_pronunciation(s["text"].strip(), pron_dict)
        mp3 = tts_segment(text, voice)
        if mp3:
            out.append({"start": float(s["start"]), "end": float(s["end"]), "text": text, "mp3": mp3, "dur": dur(mp3)})
    return out

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

def segments_to_srt(segments):
    return "\n".join([f"{i}\n{fmt_ts(s['start'])} --> {fmt_ts(s['end'])}\n{s['text']}\n" for i, s in enumerate(segments, 1)])

# ------------------------------------------------------- AI Thumbnail Generator
def generate_thumbnail_image(api_key, context, title_text, ratio, text_color, style, ref_image_bytes=None):
    aspect_map = {"16:9": "16:9 landscape format for YouTube", "9:16": "9:16 vertical layout for TikTok/Reels", "4:5": "4:5 portrait format for Facebook/Instagram"}
    prompt = f"Create an epic, high-impact YouTube clickbait thumbnail in {aspect_map.get(ratio, '16:9')}. Subject theme: {context}. "
    if title_text.strip():
        prompt += f"Boldly feature typography text: '{title_text}' using vibrant {text_color} colors. "
    prompt += f"Overall style: {style}. Highly detailed, ultra sharp, cinematic lighting."
    
    parts = [{"text": prompt}]
    if ref_image_bytes:
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(ref_image_bytes).decode("utf-8")}})
    
    url = f"{GEMINI_BASE}gemini-2.5-flash-image-preview:generateContent?key={api_key}"
    body = {"contents": [{"parts": parts}], "generationConfig": {"responseModalities": ["IMAGE"]}}
    r = requests.post(url, headers={"Content-Type": "application/json"}, json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Thumbnail API Error: {r.text[:200]}")
    b64_data = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    return base64.b64decode(b64_data)

# ------------------------------------------------------------------ Streamlit Main App
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
        st.markdown("#### 🎚️ Render & Audio ဆက်တင်")
        voice = st.selectbox("အသံရွေးချယ်ပါ", [VOICE_MALE, VOICE_FEMALE], format_func=lambda v: "🗣️ ကျား (Thiha)" if v == VOICE_MALE else "🗣️ မ (Nilar)")
        speedup = st.slider("⚡ Render ပြီးရင် Speed တင် (1.0x - 2.0x)", 1.0, 2.0, 1.0, 0.05, help="ဗီဒီယိုနှင့် မြန်မာအသံကို တစ်ပြိုင်နက် 2.0x အထိ အမြန်နှုန်း တင်ပေးပါမည်")
        burn_subs = st.checkbox("📝 Video Final တွင် Subtitle တခါတည်းထိုးမည်", value=True, help="အမှန်ခြစ်ထားပါက Final Video ထဲတွင် မြန်မာစာတန်းထိုး အလိုအလျောက် ပါသွားပါမည်")

        st.divider()
        with st.expander("📖 အသံထွက် အဘိဓာန် (Pronunciation)", expanded=False):
            st.caption("အသံထွက်မှားတတ်သော စာလုံးများကို အစားထိုးသတ်မှတ်ပါ:")
            new_w = st.text_input("မူရင်းစာလုံး (Word)", key="pw_w")
            new_r = st.text_input("အသံထွက်စာ (Replace)", key="pw_r")
            if st.button("➕ စာလုံးပေါင်းထည့်ရန်"):
                if new_w and new_r:
                    st.session_state.pron_dict.append({"word": new_w, "replace": new_r})
                    st.success("ထည့်သွင်းပြီးပါပြီ!")
            st.write(st.session_state.pron_dict)

    # Header
    st.markdown(
        '<div class="spidey-hero">'
        '<div class="spidey-kicker">🕸️ ALL-IN-ONE VIDEO CREATOR STUDIO 🕸️</div>'
        '<div class="spidey-title">Spidy Dub Studio</div>'
        '<div class="spidey-sub">Audio Dubbing • Titles & Captions • Subtitles • Thumbnail Maker 🕷️</div>'
        '</div>', unsafe_allow_html=True
    )

    tab_dub, tab_thumb = st.tabs(["🎙️ Audio Dub & Social Creator", "🖼️ AI Thumbnail Maker"])

    # ---------------- TAB 1: Dubbing & Assets ----------------
    with tab_dub:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown('<div class="spidey-stephead"><span class="spidey-num">1</span><span>Video တင်သွင်းပါ</span></div>', unsafe_allow_html=True)
            video_file = st.file_uploader("MP4 / MOV ဗီဒီယိုဖိုင် တင်ပါ", type=["mp4", "mov", "webm"])
        with c2:
            st.markdown('<div class="spidey-stephead"><span class="spidey-num">2</span><span>စနစ်ပြင်ဆင်မှု</span></div>', unsafe_allow_html=True)
            src_lang = st.selectbox("မူရင်းဘာသာစကား", ["Auto", "English", "Korean", "Japanese", "Chinese", "Thai"])
            lang_code = None if src_lang == "Auto" else {"English": "en", "Korean": "ko", "Japanese": "ja", "Chinese": "zh", "Thai": "th"}[src_lang]

        if video_file and st.button("🚀 ဗီဒီယို စတင်ဆန်းစစ်ပြီး Dubbing ပြုလုပ်မည်", type="primary", use_container_width=True):
            if not gemini_key or not groq_key:
                st.error("ကျေးဇူးပြု၍ Sidebar တွင် Gemini Key နှင့် Groq Key ထည့်သွင်းပါ")
                st.stop()

            run_id = uuid.uuid4().hex[:8]
            rd = os.path.join(WORK_DIR, run_id)
            os.makedirs(rd, exist_ok=True)
            vpath = os.path.join(rd, video_file.name)
            with open(vpath, "wb") as f:
                f.write(video_file.getbuffer())

            with st.status("လုပ်ငန်းစဉ် စတင်နေပါသည်...", expanded=True) as status_box:
                # 1. Audio extract
                status_box.update(label="Audio ခွဲထုတ်နေပါသည်...")
                wpath = os.path.join(rd, "audio.mp3")
                run(["ffmpeg", "-y", "-v", "error", "-i", vpath, "-ar", "16000", "-ac", "1", "-b:a", "32k", wpath])
                total_duration = dur(vpath)

                # 2. STT
                status_box.update(label="Groq Whisper ဖြင့် အသံမှ စာသားထုတ်နေပါသည်...")
                segs = transcribe_audio_groq(wpath, groq_key, lang_code)

                # 3. Translate
                status_box.update(label="Gemini ဖြင့် မြန်မာဘာသာသို့ ပြန်ဆိုနေပါသည်...")
                translations = gemini_translate(gemini_key, segs, GEMINI_MODEL_DEFAULT)
                full_script = " ".join([t["text"] for t in translations])

                # 4. Social Assets
                status_box.update(label="Titles & Description ရေးသားနေပါသည်...")
                social_meta = generate_social_assets(gemini_key, GEMINI_MODEL_DEFAULT, full_script)

                # 5. TTS & Recap Render
                status_box.update(label="မြန်မာအသံဖိုင် ဖန်တီးပြီး ဗီဒီယိုနှင့် ပေါင်းစပ်နေပါသည်...")
                natural = tts_natural(translations, voice, st.session_state.pron_dict)
                work_rc = os.path.join(rd, "recap")
                raw_mp4 = os.path.join(work_rc, "recap.mp4")
                _, timeline = render_recap_video(vpath, natural, total_duration, work_rc, raw_mp4)

                # 6. Speedup
                _stage = raw_mp4
                _subs = timeline
                if speedup > 1.0:
                    status_box.update(label=f"အမြန်နှုန်းကို {speedup}x သို့ မြှင့်တင်နေပါသည်...")
                    sped_mp4 = os.path.join(rd, "spedup.mp4")
                    speedup_video(_stage, speedup, sped_mp4)
                    _stage = sped_mp4
                    _subs = [{"start": s["start"] / speedup, "end": s["end"] / speedup, "text": s["text"]} for s in _subs]

                # 7. Subtitle Burn-in
                if burn_subs and _subs:
                    status_box.update(label="ဗီဒီယိုပေါ်တွင် မြန်မာ Subtitle စာတန်း တိုက်ရိုက်ထိုးနေပါသည်...")
                    srt_path = os.path.join(rd, "sub.srt")
                    with open(srt_path, "w", encoding="utf-8") as f:
                        f.write(segments_to_srt(_subs))
                    burned_mp4 = os.path.join(rd, "final_burned.mp4")
                    try:
                        burn_subtitles_to_video(_stage, srt_path, burned_mp4)
                        _stage = burned_mp4
                    except Exception as e:
                        st.warning(f"Subtitle burn error: {e}")

                final_out = os.path.join(rd, "final_video.mp4")
                shutil.copyfile(_stage, final_out)
                status_box.update(label="အားလုံးပြီးမြောက်ပါပြီ!", state="complete")

            st.success("🎉 အောင်မြင်စွာ ဖန်တီးပြီးပါပြီ!")
            st.video(final_out)

            # Titles & Description Display
            with st.expander("🔥 Social Media အတွက် ခေါင်းစဉ် ၅ ခု နှင့် Caption (နှိပ်ကြည့်ရန်)", expanded=True):
                st.subheader("📌 အကြံပြု ခေါင်းစဉ်များ (Titles with Tags):")
                for t in social_meta.get("titles", []):
                    st.code(t, language="text")
                st.subheader("📝 Caption / Description:")
                st.code(social_meta.get("description", ""), language="text")

            # Downloads
            d1, d2 = st.columns(2)
            with d1:
                with open(final_out, "rb") as f:
                    st.download_button("⬇️ Download Dubbed Video (MP4)", f, file_name="Spidy_Dubbed.mp4", mime="video/mp4", use_container_width=True)
            with d2:
                st.download_button("⬇️ Download SRT Subtitle", segments_to_srt(_subs), file_name="Spidy_Sub.srt", mime="text/plain", use_container_width=True)

    # ---------------- TAB 2: AI Thumbnail Maker ----------------
    with tab_thumb:
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">🎨</span><span>AI Thumbnail ဖန်တီးရန်</span></div>', unsafe_allow_html=True)
        th_context = st.text_area("Thumbnail အကြောင်းအရာ (Topic / Concept)", placeholder="ဥပမာ - ရန်သူမသိအောင် တိုက်ခိုက်နိုင်တဲ့ B-2 Spirit ကိုယ်ပျောက်ဗုံးကြဲလေယာဉ်...")
        th_text = st.text_input("ပုံပေါ်တွင် ရေးမည့်စာသား (Title Typography - Optional)", placeholder="ဥပမာ - လျှို့ဝှက်တိုက်ခိုက်မှု...")

        c_t1, c_t2, c_t3 = st.columns(3)
        with c_t1:
            th_ratio = st.selectbox("ပုံအရွယ်အစား (Ratio)", ["16:9", "9:16", "4:5"])
        with c_t2:
            th_color = st.selectbox("စာသားအရောင် (Text Color)", ["Neon Cyan and Bright Yellow", "Pure White with Heavy Shadow", "Blood Red and Pure White", "Luxury Gold and Deep Black"])
        with c_t3:
            th_style = st.selectbox("အနုပညာစတိုင် (Art Style)", ["Epic, dramatic, and cinematic with high contrast", "Cyberpunk, neon lights, highly futuristic", "Anime style, dynamic action", "Dark, mysterious, horror style"])

        th_ref = st.file_uploader("Thumbnail ထဲ ထည့်သွင်းလိုသော ပုံ (Optional)", type=["jpg", "png", "jpeg"], key="th_uploader")

        if st.button("✨ Thumbnail ဖန်တီးမည် (Generate Thumbnail)", type="primary"):
            if not gemini_key:
                st.error("Sidebar တွင် Gemini API Key ထည့်ပါ")
            elif not th_context.strip():
                st.warning("အကြောင်းအရာ အနည်းငယ် ရိုက်ထည့်ပေးပါ")
            else:
                with st.spinner("AI မှ Thumbnail ဖန်တီးနေပါသည်..."):
                    try:
                        ref_bytes = th_ref.getbuffer().tobytes() if th_ref else None
                        img_bytes = generate_thumbnail_image(gemini_key, th_context, th_text, th_ratio, th_color, th_style, ref_bytes)
                        st.image(img_bytes, caption="Generated Thumbnail", use_container_width=True)
                        st.download_button("⬇️ Download Thumbnail (JPG)", img_bytes, file_name="Thumbnail.jpg", mime="image/jpeg")
                    except Exception as e:
                        st.error(f"Thumbnail error: {e}")

if __name__ == "__main__":
    main()

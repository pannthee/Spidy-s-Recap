#!/usr/bin/env python3
"""Spdiy Dub Studio — ဗီဒီယိုထဲက စာသားပြောအပိုင်းတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးတဲ့ tool.

RecapKit ရဲ့ Audio Dub feature ကို တစ်ယောက်စာသုံးဖို့ ပြန်ဆောက်ထားတာ။
Login မလို၊ ငွေမလို — ကိုယ့် Streamlit Cloud မှာ run တယ်။
API key တွေကို browser localStorage မှာ မှတ်ထားတယ် — တစ်ခါထည့်ရုံနဲ့
hard refresh ဆွဲလည်း မပျောက်ဘူး (server Secrets ရှိရင် အဲ့ဒါက အဓိက)။
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

/* --- ကတ် --- */
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
</style>"""

_card_ctx_stack = []

def _spidey_card_open(n, title):
    import streamlit as st
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
    ctx = _card_ctx_stack.pop()
    ctx.__exit__(None, None, None)

def _spidey_steps(S, is_video, narr=False):
    import streamlit as st
    st.markdown(
        """<style>
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
</style>""",
        unsafe_allow_html=True,
    )
    has_out = bool(
        (S.out_mp4 and os.path.isfile(S.out_mp4))
        or (S.out_mp3 and os.path.isfile(S.out_mp3))
    )
    done = [
        bool(S.video_path) if is_video else bool(S.src_segments),
        bool(S.src_segments),
        bool(S.translations),
        bool(S.final_segments),
        bool(S.fitted),
        has_out,
    ]
    cur = max(1, min(6, int(S.get("wizard_step", 1))))
    S["wizard_step"] = cur
    cols = st.columns(6)
    for i, col in enumerate(cols):
        icon = ("✅" if done[i] else
                "⏭️" if i == 1 and not is_video else
                "🔴" if i + 1 == cur else "⭕")
        with col:
            if st.button(f"{i + 1}{icon}", key=f"wiz_nav_{i}",
                         type="primary" if i + 1 == cur else "secondary",
                         use_container_width=True,
                         disabled=(i + 1 == cur)):
                S["wizard_step"] = i + 1
                st.rerun()

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3"
_SRC_LANGS = [
    ("🤖 Auto (အလိုအလျောက်)", None),
    ("🇬🇧 English", "en"),
    ("🇰🇷 Korean", "ko"),
    ("🇯🇵 Japanese", "ja"),
    ("🇨🇳 Chinese", "zh"),
    ("🇹🇭 Thai", "th"),
    ("🇻🇳 Vietnamese", "vi"),
    ("🇮🇩 Indonesian", "id"),
    ("🇪🇸 Spanish", "es"),
    ("🇫🇷 French", "fr"),
    ("🇩🇪 German", "de"),
    ("🇷🇺 Russian", "ru"),
    ("🇮🇳 Hindi", "hi"),
]
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
VOICE_MALE = "my-MM-ThihaNeural"
VOICE_FEMALE = "my-MM-NilarNeural"

# ------------------------------------------------------------------ helpers
def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True)

def dur(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
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

# ------------------------------------------------------- step 2: transcribe
def transcribe_audio(audio_path, api_key, language=None, on_chunk=None):
    size = os.path.getsize(audio_path)
    if size > 20 * 1024 * 1024:
        return _transcribe_chunked(audio_path, api_key, language, on_chunk)
    return _transcribe_single(audio_path, api_key, language)

def _transcribe_single(audio_path, api_key, language=None):
    import requests
    with open(audio_path, "rb") as f:
        data = f.read()
    files = {"file": (os.path.basename(audio_path), data, "audio/mpeg")}
    form = {"model": GROQ_MODEL, "response_format": "verbose_json"}
    if language:
        form["language"] = language
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        r = requests.post(GROQ_URL, headers=headers, files=files,
                          data=form, timeout=300)
    except Exception:
        raise RuntimeError("Groq transcription timed out — network စစ်ပြီး ပြန်ကြိုးစားပါ")
    if r.status_code != 200:
        try:
            msg = r.json().get("error", {}).get("message") or f"Groq Error ({r.status_code})"
        except Exception:
            msg = f"Groq Error ({r.status_code})"
        raise RuntimeError(f"စာသားထုတ်တာ ပျက်သွားတယ် (Groq HTTP {r.status_code}): {msg}")
    body = r.json()
    segs = []
    for s in (body.get("segments") or []):
        if not isinstance(s, dict):
            continue
        text = (s.get("text") or "").strip()
        if not text:
            continue
        segs.append({"start": float(s.get("start") or 0),
                     "end": float(s.get("end") or 0), "text": text})
    return {"language": body.get("language", ""), "segments": segs}

def _transcribe_chunked(audio_path, api_key, language=None, on_chunk=None):
    total = dur(audio_path) or 0
    CHUNK_SEC = 3000.0
    n = max(2, int(total // CHUNK_SEC) + 1)
    step = total / n
    tmpdir = os.path.dirname(audio_path)
    all_segs, lang = [], ""
    for i in range(n):
        start = i * step
        chunk = os.path.join(tmpdir, f"_tchunk{i}.mp3")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.2f}",
             "-t", f"{step + 1:.2f}", "-i", audio_path, "-c", "copy", chunk])
        try:
            data = _transcribe_single(chunk, api_key, language)
        finally:
            if os.path.isfile(chunk):
                os.remove(chunk)
        if i == 0:
            lang = data.get("language", "")
        if on_chunk:
            on_chunk(i + 1, n)
        for s in data.get("segments", []):
            s = dict(s)
            s["start"] = float(s.get("start") or 0) + start
            s["end"] = float(s.get("end") or 0) + start
            all_segs.append(s)
    all_segs.sort(key=lambda s: s["start"])
    deduped = []
    for s in all_segs:
        if (deduped and abs(s["start"] - deduped[-1]["start"]) < 0.5
                and s["text"] == deduped[-1]["text"]):
            continue
        deduped.append(s)
    return {"language": lang, "segments": deduped}

_AAI_BASE = "https://api.assemblyai.com/v2"

def _aai_words_to_segments(words, max_gap=0.7, max_dur=8.0, max_words=25):
    segs, cur, cur_start = [], [], None
    for w in words:
        text = (w.get("text") or "").strip()
        if not text:
            continue
        s, e = w.get("start", 0) / 1000.0, w.get("end", 0) / 1000.0
        if cur and cur_start is not None:
            gap = s - cur[-1][1]
            d_seg = e - cur_start
            if gap > max_gap or d_seg > max_dur or len(cur) >= max_words or cur[-1][2][-1:] in ".!?":
                segs.append({"start": cur_start, "end": cur[-1][1],
                             "text": " ".join(t for _, _, t in cur)})
                cur, cur_start = [], None
        if cur_start is None:
            cur_start = s
        cur.append((s, e, text))
    if cur:
        segs.append({"start": cur_start, "end": cur[-1][1],
                     "text": " ".join(t for _, _, t in cur)})
    return [sg for sg in segs if sg["end"] > sg["start"] and sg["text"]]

def transcribe_assemblyai(audio_path, api_key, language=None, progress_cb=None,
                          poll_interval=3.0, timeout=900):
    import requests
    import time

    def _h(json_ct=False):
        h = {"authorization": api_key}
        if json_ct:
            h["content-type"] = "application/json"
        return h

    try:
        with open(audio_path, "rb") as f:
            r = requests.post(f"{_AAI_BASE}/upload", headers=_h(), data=f, timeout=300)
    except Exception:
        raise RuntimeError("AssemblyAI: ဖိုင်တင်တာ ပျက်သွားတယ် — network စစ်ပြီး ပြန်ကြိုးစားပါ")
    if r.status_code != 200:
        raise RuntimeError(f"AssemblyAI upload ပျက်သွားတယ် (HTTP {r.status_code})")
    upload_url = r.json().get("upload_url")
    if not upload_url:
        raise RuntimeError("AssemblyAI upload: upload_url ပြန်မရဘူး")

    payload = {"audio_url": upload_url, "speech_models": ["universal-2"]}
    if language:
        payload["language_code"] = language
    else:
        payload["language_detection"] = True
    try:
        r = requests.post(f"{_AAI_BASE}/transcript", headers=_h(True), json=payload, timeout=60)
    except Exception:
        raise RuntimeError("AssemblyAI: transcript တောင်းတာ ပျက်သွားတယ် — network စစ်ပါ")
    if r.status_code != 200:
        raise RuntimeError(f"AssemblyAI transcript ပျက်သွားတယ်: {r.text}")
    tid = r.json().get("id")

    waited = 0.0
    while True:
        try:
            r = requests.get(f"{_AAI_BASE}/transcript/{tid}", headers=_h(), timeout=30)
        except Exception:
            raise RuntimeError("AssemblyAI: အခြေအနေမေးတာ ပျက်သွားတယ် — network စစ်ပါ")
        body = r.json()
        status = body.get("status")
        if status == "completed":
            segs = _aai_words_to_segments(body.get("words") or [])
            return {"language": body.get("language_code", ""), "segments": segs}
        if status == "error":
            raise RuntimeError(f"AssemblyAI transcribe ပျက်သွားတယ်: {body.get('error') or 'unknown'}")
        if waited >= timeout:
            raise RuntimeError("AssemblyAI: အချိန်ကုန်သွားတယ် — ပြန်ကြိုးစားပါ")
        time.sleep(poll_interval)
        waited += poll_interval
        if progress_cb:
            progress_cb(waited)

def transcribe_with_fallback(audio_path, groq_key=None, assembly_key=None,
                             language=None, on_note=None, on_chunk=None):
    last_err = None
    if groq_key:
        try:
            return transcribe_audio(audio_path, groq_key, language, on_chunk), "groq"
        except Exception as e:
            last_err = e
            if on_note:
                on_note("Groq မရဘူး — AssemblyAI နဲ့ ဆက်လုပ်မယ်…")
    if assembly_key:
        def _cb(w):
            if on_note:
                on_note(f"AssemblyAI နားထောင်နေတယ်… ({w:.0f} စက္ကန့်)")
        data = transcribe_assemblyai(audio_path, assembly_key, language, progress_cb=_cb)
        return data, "assemblyai"
    if last_err is not None:
        raise last_err
    raise RuntimeError("Groq / AssemblyAI key တစ်ခုခု ထည့်မှ စာသားထုတ်လို့ရမယ် (ဘယ်ဘက် sidebar)။")

# ------------------------------------------------------- step 3: translate
_MYANMAR_ONLY = (
    " Write every 'text' value ONLY in Myanmar (Burmese) Unicode script — "
    "never mix in Tamil, Devanagari/Hindi, Thai, Chinese, Korean, Japanese, "
    "or any other non-Myanmar script, not even for names."
)

_HUMAN_STYLE = (
    " Write like a veteran human subtitler, NOT a translation machine. "
    "Translate MEANING, never mirror the source sentence structure — rebuild each line "
    "the way a Burmese person would actually say it out loud. One idea per line, short "
    "and speakable; cut filler the viewer can already see on screen. "
    "Match the register to each character's relationship and keep it consistent for the "
    "whole video: close friends / lovers / family → casual (ငါ/နင်); strangers, elders, "
    "bosses → polite (ကျွန်တော်/ခင်ဗျား). "
    "BANNED stiff formal connectors: ထို့ကြောင့်, သို့သော်လည်း, ထို့နောက်, ထို့အပြင် — "
    "use conversational ones instead (ဒါကြောင့်, ဒါပေမဲ့, ပြီးတော့). "
    "Localize idioms, jokes and slang into natural Burmese equivalents — never translate "
    "them literally. No em-dashes, no explanatory padding. "
    "FINAL CHECK: read each line aloud in your head — if no real Burmese speaker would say "
    "it like that, rewrite it until it sounds human."
)

_TRANSLATE_SYS = (
    "You translate video subtitle lines for Myanmar voiceover dubbing. "
    "Translate each line into natural SPOKEN Burmese (Myanmar) — the way a narrator "
    "would say it out loud, not formal written style. Keep the meaning, keep it "
    "concise (it must fit the original speaking time). Do not add explanations. "
    "Return ONLY a JSON array of objects with keys 'id' and 'text'."
    + _MYANMAR_ONLY + _HUMAN_STYLE
)

def _gemini_call(api_key, model_id, system_text, payload_text):
    import requests
    url = f"{GEMINI_BASE}{model_id}:generateContent"
    body = {
        "contents": [{"role": "user", "parts": [
            {"text": system_text}, {"text": payload_text}]}],
        "generationConfig": {"responseMimeType": "application/json",
                             "temperature": 0.3, "maxOutputTokens": 8192},
    }
    r = requests.post(url, headers={"Content-Type": "application/json",
                                    "x-goog-api-key": api_key},
                      json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini error {r.status_code}: {r.text[:300]}")
    data = r.json()
    try:
        txt = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("Gemini က မျှော်လင့်မထားတဲ့ response ပြန်တယ်")
    txt = txt.strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```(?:json)?\s*", "", txt)
        txt = re.sub(r"\s*```$", "", txt)
    return json.loads(txt.strip())

def parse_glossary(raw):
    pairs = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        a, b = line.split("=", 1)
        a, b = a.strip(), b.strip()
        if a and b:
            pairs.append((a, b))
    return pairs

def _glossary_prompt(pairs):
    if not pairs:
        return ""
    lines = "\n".join(f"- {a} → {b}" for a, b in pairs)
    return ("\nGlossary — ALWAYS use these exact Burmese forms for the "
            f"names/terms below, do not transliterate them differently:\n{lines}\n")

def gemini_translate(api_key, segments, model_id, progress_cb=None, glossary=None,
                     recap=False, story_memory=None):
    items = [{"id": i, "text": s["text"]} for i, s in enumerate(segments)]
    out = {}
    failed = []
    _sys = _TRANSLATE_SYS + _story_memory_block(story_memory) + _glossary_prompt(glossary)
    BATCH = 25
    batches = [items[i:i + BATCH] for i in range(0, len(items), BATCH)]
    for b, batch in enumerate(batches):
        try:
            res = _gemini_call(api_key, model_id, _sys, json.dumps(batch, ensure_ascii=False))
            for row in res:
                if isinstance(row, dict) and "id" in row and "text" in row:
                    out[int(row["id"])] = str(row["text"]).strip()
            missing = [x["id"] for x in batch if x["id"] not in out]
            failed.extend(missing)
        except Exception:
            failed.extend([x["id"] for x in batch])
        if progress_cb:
            progress_cb((b + 1) / len(batches))
    if failed:
        retry = [x for x in items if x["id"] in failed]
        for b, batch in enumerate([retry[i:i + BATCH] for i in range(0, len(retry), BATCH)]):
            try:
                res = _gemini_call(api_key, model_id, _sys, json.dumps(batch, ensure_ascii=False))
                for row in res:
                    if isinstance(row, dict) and "id" in row and "text" in row:
                        out[int(row["id"])] = str(row["text"]).strip()
            except Exception:
                pass
    result = []
    for i, s in enumerate(segments):
        result.append({"start": s["start"], "end": s["end"],
                       "src": s["text"], "text": out.get(i, s["text"])})
    return result, failed

def merge_tiny_segments(segments, max_gap=0.5, min_slot=1.5, max_merged=8.0):
    if not segments:
        return segments
    merged = []
    i, n = 0, len(segments)
    while i < n:
        cur = dict(segments[i])
        while (i + 1 < n
               and cur["end"] - cur["start"] < min_slot
               and segments[i + 1]["start"] - cur["end"] < max_gap
               and cur["end"] - cur["start"] < max_merged):
            nxt = segments[i + 1]
            cur["end"] = float(nxt["end"])
            cur["text"] = (cur["text"] + " " + nxt["text"]).strip()
            if "src" in cur or "src" in nxt:
                cur["src"] = ((cur.get("src") or "") + " " + (nxt.get("src") or "")).strip()
            i += 1
        merged.append(cur)
        i += 1
    return merged

# ----------------------------- browser localStorage
_LS_GEMINI = "audiodub_gemini_key"
_LS_GROQ = "audiodub_groq_key"
_LS_ASSEMBLYAI = "audiodub_assemblyai_key"
_LS_GLOSSARY = "audiodub_glossary"

def _local_storage(st):
    try:
        from streamlit_local_storage import LocalStorage
        return LocalStorage(key="audiodub_ls")
    except Exception:
        return None

def _ls_get(localS, k):
    try:
        return (localS.getItem(k) or "").strip() if localS else ""
    except Exception:
        return ""

def _ls_set(localS, k, v, ckey):
    try:
        if localS and v:
            localS.setItem(k, v, key=ckey)
    except Exception:
        pass

def _ls_del(localS, k, ckey):
    try:
        if localS:
            localS.eraseItem(k, key=ckey)
            try:
                localS.storedItems.pop(k, None)
            except Exception:
                pass
    except Exception:
        pass

# ------------------------------------------------- step 5: TTS + slot fit
def _valid_audio(path):
    return os.path.isfile(path) and os.path.getsize(path) > 1000

async def _edge_save(text, voice, path):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(path)

def tts_segment(text, voice_primary=VOICE_MALE, voice_fallback=VOICE_FEMALE):
    key = hashlib.sha1(f"edge:{voice_primary}:{text}".encode("utf-8")).hexdigest()[:16]
    out = os.path.join(CACHE_TTS, f"{key}.mp3")
    if _valid_audio(out):
        return out
    for voice in (voice_primary, voice_fallback):
        try:
            asyncio.run(_edge_save(text, voice, out))
            if _valid_audio(out):
                return out
        except Exception:
            continue
    return None

def fit_segment(src_mp3, slot, gap_after, max_speed, out_path):
    d = dur(src_mp3)
    ratio = d / slot if slot > 0 else 1.0
    filters = []
    if ratio <= 1.0:
        filters.append(f"apad=whole_dur={slot:.3f}")
        filters.append(f"atrim=duration={slot:.3f}")
        target, note = slot, "natural"
    elif ratio <= max_speed:
        filters.append(f"atempo={ratio:.4f}")
        target, note = slot, f"x{ratio:.2f}"
    else:
        filters.append(f"atempo={max_speed:.4f}")
        target = min(d / max_speed, slot + gap_after)
        note = "overflow"
    filters.append(f"atrim=duration={target:.3f}")
    run(["ffmpeg", "-y", "-v", "error", "-i", src_mp3,
         "-af", ",".join(filters), "-ar", "24000", "-ac", "1", out_path])
    return target, note, ratio

def tts_and_fit(segments, voice, max_speed, work_segs, progress_cb=None, tts_fn=None):
    tts_fn = tts_fn or tts_segment
    os.makedirs(work_segs, exist_ok=True)
    fitted, report = [], {"natural": 0, "sped": 0, "overflow": [], "tts_failed": []}
    n = len(segments)
    for i, s in enumerate(segments):
        start, end, text = s["start"], s["end"], s["text"].strip()
        slot = end - start
        next_start = segments[i + 1]["start"] if i + 1 < n else end
        gap_after = max(0.0, next_start - end)
        src = tts_fn(text, voice, VOICE_FEMALE) if tts_fn is tts_segment else tts_fn(text)
        if src is None:
            report["tts_failed"].append((i, start, text[:60]))
        else:
            seg_path = os.path.join(work_segs, f"s{i:04d}.mp3")
            played, note, ratio = fit_segment(src, slot, gap_after, max_speed, seg_path)
            fitted.append((start, seg_path, played))
            if note == "natural":
                report["natural"] += 1
            elif note == "overflow":
                report["overflow"].append((i, start, end, text, ratio))
            else:
                report["sped"] += 1
        if progress_cb:
            progress_cb((i + 1) / n, i, text[:50])
    return fitted, report

# ------------------------------------------------- step 6: assemble + mux
def assemble_dubbed(fitted, total_duration, work_asm, out_mp3):
    os.makedirs(work_asm, exist_ok=True)
    lst = os.path.join(work_asm, "concat.txt")
    gap_cache = {}

    def gap_file(gap):
        key = round(gap, 2)
        if key not in gap_cache:
            gf = os.path.join(work_asm, f"_gap{key}.mp3")
            if not os.path.exists(gf):
                silence(gf, key)
            gap_cache[key] = gf
        return gap_cache[key]

    with open(lst, "w") as fh:
        if fitted and fitted[0][0] > 0.02:
            fh.write(f"file '{gap_file(fitted[0][0])}'\n")
        for j, (start, seg, played) in enumerate(fitted):
            fh.write(f"file '{seg}'\n")
            next_s = fitted[j + 1][0] if j + 1 < len(fitted) else total_duration
            gap = next_s - (start + played)
            if gap > 0.02:
                fh.write(f"file '{gap_file(gap)}'\n")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c:a", "libmp3lame", "-b:a", "96k",
         "-ar", "24000", "-ac", "1", out_mp3])
    return out_mp3

def mux_video(video_path, dubbed_mp3, out_mp4):
    run(["ffmpeg", "-y", "-v", "error", "-i", video_path, "-i", dubbed_mp3,
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
         "-shortest", out_mp4])
    return out_mp4

def tts_natural(segments, voice, work_segs, progress_cb=None):
    os.makedirs(work_segs, exist_ok=True)
    out, failed = [], []
    n = len(segments)
    for i, s in enumerate(segments):
        text = s["text"].strip()
        mp3 = tts_segment(text, voice, VOICE_FEMALE) if text else None
        if mp3 is None:
            failed.append((i, s["start"], text[:60]))
        else:
            out.append({"start": float(s["start"]), "end": float(s["end"]),
                        "text": text, "mp3": mp3, "dur": dur(mp3)})
        if progress_cb:
            progress_cb((i + 1) / n, i, text[:50])
    return out, failed

def _video_fps(path):
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path],
            capture_output=True, text=True, timeout=15)
        num, den = r.stdout.strip().split("/")
        f = float(num) / float(den)
        if 1.0 < f < 120.0:
            return f
    except Exception:
        pass
    return 30.0

def render_recap_video(video_path, natural, total_duration, work_dir, out_mp4):
    if not natural:
        raise ValueError("recap render: narration အပိုင်း မရှိဘူး")
    os.makedirs(work_dir, exist_ok=True)
    n = len(natural)

    def _boundary(i):
        b = natural[i + 1]["start"] if i + 1 < n else total_duration
        return max(b, natural[i]["end"])

    pieces = []
    if natural[0]["start"] > 0.05:
        pieces.append((0.0, natural[0]["start"], natural[0]["start"]))
    for i, sg in enumerate(natural):
        b = _boundary(i)
        p_dur = b - sg["start"]
        gap = max(0.0, b - sg["end"])
        pieces.append((sg["start"], b, sg["dur"] + gap))

    fparts, vlabels = [], []
    for j, (a, b, target) in enumerate(pieces):
        p_dur = b - a
        factor = target / p_dur if p_dur > 0.05 else 1.0
        factor = min(max(factor, 0.05), 20.0)
        fparts.append(
            f"[0:v]trim=start={a:.3f}:end={b:.3f},"
            f"settb=AVTB,setpts=(PTS-STARTPTS)*{factor:.4f}[v{j}]")
        vlabels.append(f"[v{j}]")
    fcomplex = (";".join(fparts) + ";" + "".join(vlabels) +
                f"concat=n={len(pieces)}:v=1:a=0,"
                f"fps={_video_fps(video_path):.2f}[vout]")

    lst = os.path.join(work_dir, "recap_audio.txt")
    gap_cache = {}

    def gap_file(g):
        key = round(g, 2)
        if key not in gap_cache:
            gf = os.path.join(work_dir, f"_rgap{key}.mp3")
            if not os.path.exists(gf):
                silence(gf, key)
            gap_cache[key] = os.path.abspath(gf)
        return gap_cache[key]

    with open(lst, "w") as fh:
        if natural[0]["start"] > 0.05:
            fh.write(f"file '{gap_file(natural[0]['start'])}'\n")
        for i, sg in enumerate(natural):
            fh.write(f"file '{os.path.abspath(sg['mp3'])}'\n")
            gap = max(0.0, _boundary(i) - sg["end"])
            if gap > 0.02:
                fh.write(f"file '{gap_file(gap)}'\n")

    run(["ffmpeg", "-y", "-v", "error", "-i", video_path,
         "-f", "concat", "-safe", "0", "-i", lst,
         "-filter_complex", fcomplex,
         "-map", "[vout]", "-map", "1:a:0",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", "-shortest", out_mp4])

    timeline, report, cum = [], [], 0.0
    if natural[0]["start"] > 0.05:
        cum = natural[0]["start"]
    for i, sg in enumerate(natural):
        b = _boundary(i)
        p_dur = b - sg["start"]
        target = sg["dur"] + max(0.0, b - sg["end"])
        factor = target / p_dur if p_dur > 0.05 else 1.0
        note = ""
        if factor < 0.5:
            note = "အရမ်းနှေး (slow-mo)"
        elif factor > 2.0:
            note = "အရမ်းမြန်"
        report.append((i, factor, note))
        timeline.append({"start": cum, "end": cum + sg["dur"], "text": sg["text"]})
        cum += target
    return out_mp4, timeline, report

def speedup_video(video_in, factor, out_mp4):
    """Render ပြီးသား video ကို factor (အမြင့်ဆုံး 2.0x ထိ) အမြန်ပေး."""
    if abs(factor - 1.0) < 1e-6:
        shutil.copyfile(video_in, out_mp4)
        return out_mp4
    run(["ffmpeg", "-y", "-v", "error", "-i", video_in,
         "-vf", f"setpts=PTS/{factor:.4f}",
         "-af", f"atempo={factor:.4f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-c:a", "aac", "-b:a", "128k",
         "-movflags", "+faststart", out_mp4])
    return out_mp4

def burn_subtitles_to_video(video_in, srt_path, out_mp4):
    """ဗီဒီယိုပေါ်တွင် မြန်မာ Subtitle စာတန်းကို တိုက်ရိုက် Burn-in ထိုးပေးခြင်း."""
    escaped_srt = os.path.abspath(srt_path).replace("\\", "/").replace(":", "\\:")
    sub_filter = (
        f"subtitles='{escaped_srt}':force_style='FontName=Noto Sans Myanmar,FontSize=16,"
        f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,MarginV=25'"
    )
    run(["ffmpeg", "-y", "-v", "error", "-i", video_in,
         "-vf", sub_filter,
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
         "-c:a", "copy",
         "-movflags", "+faststart", out_mp4])
    return out_mp4

def segments_to_srt(segments):
    lines = []
    for i, s in enumerate(segments, 1):
        lines.append(f"{i}\n{fmt_ts(s['start'])} --> {fmt_ts(s['end'])}\n{s['text']}\n")
    return "\n".join(lines)

_SRT_TS_LINE = re.compile(r"(\d+:[\d:.,]+)\s*-->\s*(\d+:[\d:.,]+)")

def parse_srt(text):
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    segs = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.strip().split("\n") if l.strip()]
        if not lines:
            continue
        ts_idx = 0
        if "-->" not in lines[0] and len(lines) > 1:
            ts_idx = 1
        m = _SRT_TS_LINE.search(lines[ts_idx]) if ts_idx < len(lines) else None
        if not m:
            continue
        try:
            start, end = parse_ts(m.group(1)), parse_ts(m.group(2))
        except (ValueError, IndexError):
            continue
        txt = " ".join(l.strip() for l in lines[ts_idx + 1:] if l.strip())
        if end > start and txt:
            segs.append({"start": start, "end": end, "text": txt})
    segs.sort(key=lambda x: x["start"])
    return segs

_REVIEW_LINE = re.compile(r"(\d+:\d+:[\d.,]+)\s*-->\s*(\d+:[\d:.,]+)\s*\|\s*(.*)")

def segments_to_review_text(segments):
    return "\n".join(f"{fmt_ts(s['start'])} --> {fmt_ts(s['end'])} | {s['text']}" for s in segments)

def parse_review_text(raw):
    segs = []
    for ln, line in enumerate(raw.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        m = _REVIEW_LINE.match(line)
        if not m:
            raise ValueError(f"လိုင်း {ln} ပုံစံမှားနေတယ်: {line[:60]}")
        start, end, text = parse_ts(m.group(1)), parse_ts(m.group(2)), m.group(3).strip()
        if end <= start or not text:
            raise ValueError(f"လိုင်း {ln} အချိန်/စာသား မှားနေတယ်")
        segs.append({"start": start, "end": end, "text": text})
    segs.sort(key=lambda x: x["start"])
    if not segs:
        raise ValueError("စာသားတစ်ကြောင်းမှ မကျန်ဘူး")
    return segs

_FOREIGN_SCRIPT_RE = re.compile(r"[\u0B80-\u0BFF\u0900-\u097F\u0E00-\u0E7F\u3040-\u30FF\uAC00-\uD7AF\u4E00-\u9FFF]")
_FOREIGN_SCRIPT_NAMES = (
    (0x0B80, 0x0BFF, "Tamil"), (0x0900, 0x097F, "Devanagari"),
    (0x0E00, 0x0E7F, "Thai"), (0x3040, 0x30FF, "Japanese"),
    (0xAC00, 0xD7AF, "Korean"), (0x4E00, 0x9FFF, "Chinese"),
)

def _foreign_script_name(text):
    for ch in text:
        o = ord(ch)
        for lo, hi, name in _FOREIGN_SCRIPT_NAMES:
            if lo <= o <= hi:
                return name
    return "တခြား"

_EST_CPS = 14.0

def find_problem_lines(segments, max_speed):
    flags = []
    for i, s in enumerate(segments):
        slot = s["end"] - s["start"]
        text = (s["text"] or "").strip()
        reasons = []
        if not text:
            reasons.append("စာသားလွတ်နေတယ်")
        else:
            if slot > 0 and len(text) > slot * _EST_CPS * max_speed:
                reasons.append("ရှည်လွန်းတယ် (အသံထွက်ရင် အချိန်မလောက်နိုင်ဘူး)")
            if _FOREIGN_SCRIPT_RE.search(text):
                reasons.append(f"{_foreign_script_name(text)} စာလုံး ပါနေတယ်")
            src = (s.get("src") or "").strip()
            if src and text == src and re.search(r"[A-Za-z]{3,}", text):
                reasons.append("ဘာသာမပြန်ရသေးဘူး (မူရင်းအတိုင်း ကျန်နေတယ်)")
        if reasons:
            flags.append((i, " + ".join(reasons)))
    return flags

def _qc_bad_reason(text):
    t = (text or "").strip()
    if not t:
        return "စာသားလွတ်နေတယ်"
    if _FOREIGN_SCRIPT_RE.search(t):
        return f"{_foreign_script_name(t)} စာလုံး ပါနေတယ်"
    if not re.search(r"[\u1000-\u109F]", t) and re.search(r"[A-Za-z]{3,}", t):
        return "ဘာသာမပြန်ရသေးဘူး (မူရင်းအတိုင်း ကျန်နေတယ်)"
    return None

def _qc_retranslate_sys(glossary=None, story_memory=None):
    return (
        "You translate ONE video subtitle line into natural SPOKEN Burmese (Myanmar). "
        "Output ONLY Myanmar (Burmese) Unicode script — never mix in other scripts. "
        "Keep the meaning, keep it concise. Return ONLY a JSON object with key 'text'."
        + _HUMAN_STYLE + _story_memory_block(story_memory) + _glossary_prompt(glossary)
    )

def qc_retranslate(api_key, model_id, translations, glossary=None,
                   progress_cb=None, max_retries=2, story_memory=None):
    n = len(translations)
    bad = {i: _qc_bad_reason(sg.get("text", "")) for i, sg in enumerate(translations) if _qc_bad_reason(sg.get("text", ""))}
    report = {"checked": n, "bad_initial": len(bad), "bad_ratio": (len(bad) / n) if n else 0.0,
              "retried": [], "fixed": [], "still_bad": []}
    if not bad:
        return translations, report
    sys_prompt = _qc_retranslate_sys(glossary, story_memory)
    total = len(bad)
    for k, (i, reason) in enumerate(bad.items()):
        src = translations[i].get("src", "") or translations[i].get("text", "")
        if not src.strip():
            report["still_bad"].append((i, reason, ""))
            continue
        ok = False
        for _ in range(max_retries):
            try:
                res = _gemini_call(api_key, model_id, sys_prompt, json.dumps([{"id": 0, "text": src}], ensure_ascii=False))
                if res and isinstance(res[0], dict) and res[0].get("text"):
                    new_text = str(res[0]["text"]).strip()
                    if not _qc_bad_reason(new_text):
                        translations[i]["text"] = new_text
                        ok = True
                        break
            except Exception:
                pass
        report["retried"].append(i)
        if ok:
            report["fixed"].append(i)
        else:
            report["still_bad"].append((i, _qc_bad_reason(translations[i].get("text", "")) or reason, src[:80]))
        if progress_cb:
            progress_cb((k + 1) / total)
    return translations, report

def _reset_review_keys(S):
    if "review_text" in S:
        del S["review_text"]
    for k in [k for k in S.keys() if k.startswith("fixline_")]:
        del S[k]

# ------------------------------------------------- ⚡ Auto mode checkpoints
_AUTO_SPEEDUP = 1.3
_AUTO_QC_BREAK_RATIO = 0.30

def _ckpt_path(run_id, name):
    return os.path.join(WORK_DIR, run_id, "ckpt", name + ".json")

def _ckpt_save(run_id, name, data):
    d = os.path.dirname(_ckpt_path(run_id, name))
    os.makedirs(d, exist_ok=True)
    tmp = _ckpt_path(run_id, name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, _ckpt_path(run_id, name))

def _ckpt_load(run_id, name):
    p = _ckpt_path(run_id, name)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _ckpt_matches(ckpt, want):
    if not isinstance(ckpt, dict):
        return False
    return all(ckpt.get(k) == v for k, v in want.items())

def _video_fingerprint(video_path):
    try:
        return f"{os.path.basename(video_path)}::{os.path.getsize(video_path)}"
    except Exception:
        return ""

def _find_prior_run(fingerprint):
    if not fingerprint or not os.path.isdir(WORK_DIR):
        return None
    for rid in sorted(os.listdir(WORK_DIR)):
        rd = os.path.join(WORK_DIR, rid)
        if not os.path.isdir(rd):
            continue
        meta = _ckpt_load(rid, "meta")
        if meta and meta.get("fingerprint") == fingerprint:
            if not os.path.isfile(os.path.join(rd, "dubbed_video.mp4")):
                return rid
    return None

def _auto_adopt_run(S, run_id):
    meta = _ckpt_load(run_id, "meta") or {}
    S.update(run_id=run_id, video_path=meta.get("video_path"), audio_path=meta.get("audio_path"),
             duration=meta.get("duration", 0.0), dl_base=meta.get("dl_base", ""),
             _auto_up_name=meta.get("up_name", ""), src_segments=None, translations=None,
             final_segments=None, out_mp4=None, out_subs=None, auto_mp3=None,
             auto_done=False, auto_report=None)

MEM_DIR = os.path.join(WORK_DIR, "memories")

def _mem_path(name):
    safe = re.sub(r"[^\w\- ]", "", (name or "")).strip()[:60] or "drama"
    return os.path.join(MEM_DIR, safe + ".json")

def load_story_memory(name):
    if not name or not os.path.isfile(_mem_path(name)):
        return None
    try:
        with open(_mem_path(name), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def save_story_memory(name, mem):
    if not name:
        return
    os.makedirs(MEM_DIR, exist_ok=True)
    mem = dict(mem or {})
    mem["drama"] = name
    tmp = _mem_path(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(mem, f, ensure_ascii=False, indent=1)
    os.replace(tmp, _mem_path(name))

def delete_story_memory(name):
    try:
        os.remove(_mem_path(name))
    except Exception:
        pass

def _mem_fingerprint(mem):
    if not mem:
        return ""
    try:
        return hashlib.md5(json.dumps(mem.get("characters"), ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    except Exception:
        return ""

def _story_memory_block(mem):
    if not mem:
        return ""
    out = []
    chars = [c for c in (mem.get("characters") or []) if isinstance(c, dict) and c.get("src") and c.get("mm")]
    if chars:
        out.append("CHARACTER NAME MEMORY — use these EXACT Myanmar names:")
        for c in chars:
            out.append(f"- {c['src']} → {c['mm']}" + (f" ({c['role']})" if c.get("role") else ""))
    return ("\n" + "\n".join(out) + "\n") if out else ""

def build_story_memory(api_key, model_id, segments):
    full = "\n".join(s.get("text", "") for s in segments)
    mem = {"characters": [], "places": [], "terms": []}
    sys_prompt = "You read a video transcript and build a CAST/TERM MEMORY as JSON with keys 'characters', 'places', 'terms'."
    try:
        res = _gemini_call(api_key, model_id, sys_prompt, full[:24000])
        if isinstance(res, dict):
            for k in ("characters", "places", "terms"):
                for e in (res.get(k) or []):
                    if isinstance(e, dict) and e.get("src"):
                        mem[k].append({"src": e["src"], "role": e.get("role", ""), "mm": ""})
    except Exception:
        pass
    return mem

def update_story_memory(api_key, model_id, mem, translations):
    mem = dict(mem or {"characters": [], "places": [], "terms": []})
    pairs = "\n".join(f"SRC: {t.get('src', '')} | MM: {t.get('text', '')}" for t in translations[:60])
    sys_prompt = "Find matching Myanmar names for characters in memory list. Return JSON."
    try:
        res = _gemini_call(api_key, model_id, sys_prompt, pairs)
        if isinstance(res, dict):
            for k in ("characters", "places", "terms"):
                for e in (res.get(k) or []):
                    hit = next((x for x in mem.get(k, []) if x.get("src") == e.get("src")), None)
                    if hit and e.get("mm"):
                        hit["mm"] = e["mm"]
    except Exception:
        pass
    return mem

# ------------------------------------------------------------------ UI
def _init_state(st):
    defaults = {
        "run_id": None, "video_path": None, "audio_path": None, "duration": 0.0,
        "src_segments": None, "translations": None, "final_segments": None,
        "fitted": None, "fit_report": None, "out_mp4": None, "out_mp3": None,
        "lang": "", "auto_shortened": False, "srt_name": "", "srt_is_my": False,
        "dl_base": "", "scenes": None, "scene_descs": None,
        "recap_timeline": None, "recap_report": None, "out_subs": None, "wizard_step": 1,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def main():
    import streamlit as st
    st.set_page_config(page_title="Audio Dub Studio", page_icon="🕷️", layout="wide")
    st.markdown(_SPIDEY_CSS, unsafe_allow_html=True)
    _init_state(st)
    S = st.session_state

    # ---------------------------------------------------------- sidebar
    with st.sidebar:
        st.markdown("### 🕷️ Spidey Control")
        localS = _local_storage(st)

        if S.get("_clear_keys"):
            _ls_del(localS, _LS_GEMINI, "ls_del_gemini")
            _ls_del(localS, _LS_GROQ, "ls_del_groq")
            _ls_del(localS, _LS_ASSEMBLYAI, "ls_del_aai")
            for _k in ("gemini_key", "groq_key", "assemblyai_key"):
                if _k in S:
                    del S[_k]
            del S["_clear_keys"]

        st.markdown("#### 🔑 API Keys")
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not env_key and "gemini_key" not in S:
            _sg = _ls_get(localS, _LS_GEMINI)
            if _sg:
                S["gemini_key"] = _sg
        key_input = st.text_input("Gemini API Key", type="password", key="gemini_key", placeholder="AIzaSy...")
        typed_gemini = key_input.strip()
        if typed_gemini and typed_gemini != _ls_get(localS, _LS_GEMINI):
            _ls_set(localS, _LS_GEMINI, typed_gemini, "ls_set_gemini")
        api_key = typed_gemini or env_key

        env_groq = os.environ.get("GROQ_API_KEY", "").strip()
        if not env_groq and "groq_key" not in S:
            _sq = _ls_get(localS, _LS_GROQ)
            if _sq:
                S["groq_key"] = _sq
        groq_input = st.text_input("Groq API Key", type="password", key="groq_key", placeholder="gsk_...")
        typed_groq = groq_input.strip()
        if typed_groq and typed_groq != _ls_get(localS, _LS_GROQ):
            _ls_set(localS, _LS_GROQ, typed_groq, "ls_set_groq")
        groq_key = typed_groq or env_groq

        env_aai = os.environ.get("ASSEMBLYAI_API_KEY", "").strip()
        if not env_aai and "assemblyai_key" not in S:
            _sa = _ls_get(localS, _LS_ASSEMBLYAI)
            if _sa:
                S["assemblyai_key"] = _sa
        aai_input = st.text_input("AssemblyAI API Key", type="password", key="assemblyai_key", placeholder="...")
        typed_aai = aai_input.strip()
        if typed_aai and typed_aai != _ls_get(localS, _LS_ASSEMBLYAI):
            _ls_set(localS, _LS_ASSEMBLYAI, typed_aai, "ls_set_aai")
        assembly_key = typed_aai or env_aai

        st.divider()
        st.markdown("#### 🎚️ အသံ & Video ဆက်တင်")
        model_id = st.text_input("Gemini model", value=GEMINI_MODEL_DEFAULT)
        max_speed = 1.3
        voice = st.selectbox("အသံ", [VOICE_MALE, VOICE_FEMALE],
                             format_func=lambda v: "🗣️ ကျား (Thiha)" if v == VOICE_MALE else "🗣️ မ (Nilar)")

        st.markdown("##### ⚡ Output Options")
        recap_render = st.checkbox("🎞️ Recap render — video ကို narration အရှည်နဲ့ကိုက်အောင် ချိန်", value=True)
        # ⚡ 2.0x ထိ တင်နိုင်သော slider
        speedup = st.slider("⚡ Render ပြီးရင် Speed တင်ရန်", 1.0, 2.0, 1.0, 0.05,
                            help="ဗီဒီယိုနှင့် အသံကို ပုံမှန် 1.0x မှ 2.0x အထိ အမြန်နှုန်း မြှင့်တင်ပေးပါမည်")
        # 📝 Video Final တွင် Subtitle ထိုးပေးမည့် switch
        burn_subs = st.checkbox("📝 Video Final တွင် Subtitle တခါတည်းထိုးမည် (Burn-in)", value=True,
                                help="အမှန်ခြစ်ထားပါက ဗီဒီယိုပေါ်တွင် မြန်မာစာတန်းထိုး အလိုအလျောက် ပါသွားပါမည်")

        st.markdown("##### 📖 နာမည်စာရင်း (Glossary)")
        glossary_raw = st.text_area("ဇာတ်ကောင်နာမည်များ (John=ဂျွန်)", key="glossary", height=80)
        glossary = parse_glossary(glossary_raw)

        if st.button("အစက ပြန်စ", use_container_width=True):
            for k in list(S.keys()):
                del S[k]
            st.rerun()

    # ---------------------------------------------------------- main
    st.markdown(
        '<div class="spidey-hero">'
        '<div class="spidey-kicker">🕸️ FRIENDLY NEIGHBORHOOD DUBBING 🕸️</div>'
        '<div class="spidey-title">Spidy Dub Studio</div>'
        '<div class="spidey-sub">ဗီဒီယို / SRT → မြန်မာအသံ — မူရင်းအချိန်အတိုင်း 🕷️</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    mode = st.radio("အရင်းအမြစ်", ["🎬 ဗီဒီယို", "📄 SRT ဖိုင်"], horizontal=True, key="src_mode")
    is_video = (mode == "🎬 ဗီဒီယို")
    _spidey_steps(S, is_video)

    # ---- အဆင့် ၁
    if S["wizard_step"] == 1:
        _spidey_card_open(1, "ဗီဒီယိုတင်ပါ" if is_video else "SRT ဖိုင်တင်ပါ")
        if is_video:
            up = st.file_uploader("MP4 / MOV / WEBM ဖိုင်ရွေးပါ", type=["mp4", "mov", "webm"])
            if up is not None:
                if st.button("▶️ အသံထုတ်ယူရန်", type="primary", use_container_width=True):
                    run_id = uuid.uuid4().hex[:8]
                    rd = os.path.join(WORK_DIR, run_id)
                    os.makedirs(rd, exist_ok=True)
                    vpath = os.path.join(rd, up.name)
                    with open(vpath, "wb") as f:
                        f.write(up.getbuffer())
                    wpath = os.path.join(rd, "audio.mp3")
                    with st.status("ffmpeg နဲ့ အသံထုတ်နေတယ်...", expanded=False):
                        run(["ffmpeg", "-y", "-v", "error", "-i", vpath,
                             "-ar", "16000", "-ac", "1", "-b:a", "32k", wpath])
                        d = dur(vpath)
                    S.update(run_id=run_id, video_path=vpath, audio_path=wpath, duration=d,
                             src_segments=None, translations=None, final_segments=None,
                             fitted=None, fit_report=None, out_mp4=None, out_mp3=None,
                             dl_base=os.path.splitext(up.name)[0])
                    st.toast("✅ အသံထုတ်ပြီးပါပြီ")
                    S["wizard_step"] = 2
                    st.rerun()
        else:
            srt_up = st.file_uploader("SRT ဖိုင်ရွေးပါ", type=["srt"], key="srt_up")
            if srt_up is not None and st.button("▶️ SRT ဖတ်ရန်", type="primary", use_container_width=True):
                raw = srt_up.getbuffer()
                text = bytes(raw).decode("utf-8-sig", errors="ignore")
                segs = parse_srt(text)
                run_id = uuid.uuid4().hex[:8]
                S.update(run_id=run_id, video_path=None, audio_path=None, duration=segs[-1]["end"],
                         src_segments=segs, translations=None, final_segments=None,
                         dl_base=os.path.splitext(srt_up.name)[0])
                S["wizard_step"] = 3
                st.rerun()
        _spidey_card_close()

    # ---- အဆင့် ၂
    if S["wizard_step"] == 2:
        _spidey_card_open(2, "အသံမှ စာသားထုတ်")
        if not is_video:
            st.info("SRT ဖိုင်သုံးထား၍ အဆင့် ၃ သို့ ဆက်သွားပါ")
        elif not (groq_key or assembly_key):
            st.warning("Groq / AssemblyAI API Key လိုအပ်ပါသည်")
        else:
            _lang_label = st.pills("🎙️ မူရင်းဘာသာစကား", [lbl for lbl, _ in _SRC_LANGS], default="🤖 Auto (အလိုအလျောက်)")
            _lang_code = dict(_SRC_LANGS)[_lang_label]
            if st.button("🎤 နားထောင်ပြီး စာသားထုတ်ရန်", type="primary", use_container_width=True):
                with st.status("နားထောင်နေသည်...", expanded=True) as stt:
                    data, _ = transcribe_with_fallback(S.audio_path, groq_key, assembly_key, language=_lang_code)
                    segs = [{"start": x["start"], "end": x["end"], "text": x["text"]} for x in data.get("segments", [])]
                    S.src_segments = merge_tiny_segments(segs)
                    stt.update(state="complete")
                st.toast(f"✅ အပိုင်း {len(S.src_segments)} ခု တွေ့ရှိပါသည်")
                S["wizard_step"] = 3
                st.rerun()
        _spidey_card_close()

    # ---- အဆင့် ၃
    if S["wizard_step"] == 3:
        _spidey_card_open(3, "မြန်မာလို ဘာသာပြန်")
        if not S.src_segments:
            st.caption("အရင်အဆင့်များ အရင်လုပ်ပါ")
        elif not api_key:
            st.warning("Gemini API key ထည့်ပါ")
        else:
            if st.button("🌐 သဘာဝကျသော မြန်မာစကားပြော ပြန်ရန်", type="primary", use_container_width=True):
                prog = st.progress(0.0)
                result, _ = gemini_translate(api_key, S.src_segments, model_id.strip() or GEMINI_MODEL_DEFAULT,
                                             progress_cb=lambda f: prog.progress(f), glossary=glossary)
                S.translations = result
                prog.empty()
                st.toast("✅ ဘာသာပြန်ပြီးပါပြီ")
                S["wizard_step"] = 4
                st.rerun()
        _spidey_card_close()

    # ---- အဆင့် ၄
    if S["wizard_step"] == 4:
        _spidey_card_open(4, "စာသားစစ် / ပြင်")
        if not S.translations:
            st.caption("အရင်အဆင့်တွင် ဘာသာပြန်ပါ")
        else:
            raw = st.text_area("စာသားများ ပြင်ဆင်နိုင်ပါသည်:", value=segments_to_review_text(S.translations), height=250)
            if st.button("✔️ စစ်ပြီး ဆက်ရန်", type="primary", use_container_width=True):
                S.final_segments = parse_review_text(raw)
                st.toast("✅ အတည်ပြုပြီးပါပြီ")
                S["wizard_step"] = 5
                st.rerun()
        _spidey_card_close()

    # ---- အဆင့် ၅
    if S["wizard_step"] == 5:
        _spidey_card_open(5, "မြန်မာအသံထုတ် + အချိန်ချိန်")
        if not S.final_segments:
            st.caption("အရင်အဆင့်တွင် စာသားအတည်ပြုပါ")
        else:
            if st.button("🔊 အသံထုတ်ရန်", type="primary", use_container_width=True):
                work_segs = os.path.join(WORK_DIR, S.run_id, "segs")
                prog = st.progress(0.0)
                fitted, report = tts_and_fit(S.final_segments, voice, max_speed, work_segs,
                                             progress_cb=lambda f, i, t: prog.progress(f))
                S.fitted, S.fit_report = fitted, report
                prog.empty()
                st.toast("✅ အသံထုတ်ပြီးပါပြီ")
                S["wizard_step"] = 6
                st.rerun()
        _spidey_card_close()

    # ---- အဆင့် ၆: assemble + download + speedup + burn-in
    if S["wizard_step"] == 6:
        _spidey_card_open(6, "ဗီဒီယိုနှင့်ပေါင်း + Subtitle + Download" if is_video else "အသံဖိုင် Download")
        if is_video:
            if st.button("🎬 အပြီးသတ် Render ပြုလုပ်ရန်", type="primary", use_container_width=True):
                work_asm = os.path.join(WORK_DIR, S.run_id, "asm")
                dubbed = os.path.join(WORK_DIR, S.run_id, "dubbed_audio.mp3")
                out = os.path.join(WORK_DIR, S.run_id, "dubbed_video.mp4")

                with st.status("ဗီဒီယိုနှင့် အသံကို ပေါင်းစပ်နေပါသည်...", expanded=True) as status_box:
                    if recap_render and S.final_segments and S.video_path:
                        work_nat = os.path.join(WORK_DIR, S.run_id, "natural")
                        natural, _ = tts_natural(S.final_segments, voice, work_nat)
                        work_rc = os.path.join(WORK_DIR, S.run_id, "recap")
                        tmp_out = os.path.join(work_rc, "recap_video.mp4")
                        _, S.recap_timeline, S.recap_report = render_recap_video(
                            S.video_path, natural, S.duration, work_rc, tmp_out)
                        _stage = tmp_out
                        _subs = [dict(s) for s in S.recap_timeline]
                    else:
                        assemble_dubbed(S.fitted, S.duration, work_asm, dubbed)
                        mux_video(S.video_path, dubbed, out)
                        _stage = out
                        _subs = [dict(s) for s in S.final_segments]

                    # ⚡ Speed-up (2.0x ထိ တင်ပေးခြင်း)
                    if speedup > 1.0:
                        status_box.update(label=f"အမြန်နှုန်း {speedup:.2f}x သို့ တင်နေပါသည်...")
                        _spd = os.path.join(WORK_DIR, S.run_id, "spedup.mp4")
                        speedup_video(_stage, speedup, _spd)
                        _stage = _spd
                        _subs = [{"start": s["start"] / speedup,
                                  "end": s["end"] / speedup,
                                  "text": s["text"]} for s in _subs]

                    # 📝 Subtitle Burn-in (ဗီဒီယိုပေါ် တိုက်ရိုက် စာတန်းထိုးခြင်း)
                    if burn_subs and _subs:
                        status_box.update(label="ဗီဒီယိုထဲသို့ Subtitle တိုက်ရိုက် ထိုးထည့်နေပါသည်...")
                        _srt_tmp = os.path.join(WORK_DIR, S.run_id, "burned.srt")
                        with open(_srt_tmp, "w", encoding="utf-8") as f:
                            f.write(segments_to_srt(_subs))
                        _burned_mp4 = os.path.join(WORK_DIR, S.run_id, "burned_sub.mp4")
                        try:
                            burn_subtitles_to_video(_stage, _srt_tmp, _burned_mp4)
                            _stage = _burned_mp4
                        except Exception as e:
                            st.warning(f"Subtitle burn-in အနည်းငယ် အမှားရှိပါသည်: {e}")

                    if _stage != out:
                        shutil.copyfile(_stage, out)
                    S.out_subs = _subs
                    S.out_mp4 = out
                    status_box.update(label="ပြီးမြောက်ပါပြီ!", state="complete")
                    st.success("✅ အားလုံး အောင်မြင်စွာ ပြီးစီးပါပြီ!")

            if S.out_mp4 and os.path.isfile(S.out_mp4):
                st.video(S.out_mp4)
                dl_name = f"{S.get('dl_base') or 'video'}_dubbed"
                with open(S.out_mp4, "rb") as f:
                    st.download_button("⬇️ Download Dubbed Video (MP4)", f,
                                       file_name=f"{dl_name}.mp4", mime="video/mp4",
                                       type="primary", use_container_width=True)
                if S.out_subs:
                    st.download_button("⬇️ Download Subtitle (SRT)", segments_to_srt(S.out_subs),
                                       file_name=f"{dl_name}.srt", mime="text/plain",
                                       use_container_width=True)
        _spidey_card_close()

    # Nav buttons
    _cur = max(1, min(6, int(S.get("wizard_step", 1))))
    st.caption(f"အဆင့် {_cur} / 6")
    b1, b2 = st.columns(2)
    with b1:
        if _cur > 1 and st.button("◀️ ပြန်သွား", key="b_back", use_container_width=True):
            S["wizard_step"] = _cur - 1
            st.rerun()
    with b2:
        if _cur < 6 and st.button("ဆက်သွား ▶️", key="b_next", type="primary", use_container_width=True):
            S["wizard_step"] = _cur + 1
            st.rerun()

if __name__ == "__main__":
    main()

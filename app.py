#!/usr/bin/env python3
"""Audio Dub Studio — ဗီဒီယိုထဲက စာသားပြောအပိုင်းတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးတဲ့ tool.

RecapKit ရဲ့ Audio Dub feature ကို တစ်ယောက်စာသုံးဖို့ ပြန်ဆောက်ထားတာ။
Login မလို၊ ငွေမလို — ကိုယ့် Streamlit Cloud မှာ run တယ်။
API key တွေကို browser localStorage မှာ မှတ်ထားတယ် — တစ်ခါထည့်ရုံနဲ့
hard refresh ဆွဲလည်း မပျောက်ဘူး (server Secrets ရှိရင် အဲ့ဒါက အဓိက)။

Pipeline:
  1. MP4 တင် → ffmpeg နဲ့ audio ထုတ် (mp3 16k mono, 32k — Groq 25MB ကန့်သတ်ချက်နဲ့ကိုက်အောင်)
  2. Groq Whisper API (whisper-large-v3-turbo) နဲ့ စာသားထုတ် (timestamp ပါ)
     ※ အရင်က local faster-whisper သုံးတာ — Streamlit Cloud ရဲ့ RAM (~1GB)
       ကန့်သတ်ချက်နဲ့ မကိုက်လို့ Groq API နဲ့ လဲထားတာ
  2b. (optional) အပိုင်းသေးလေးတွေ အလိုအလျောက်ပေါင်း — Whisper ရဲ့ 0.2s လို
      အကွက်သေးတွေကြောင့် အသံအရမ်းမြန်ရတာကို ကာကွယ်ဖို့
  3. Gemini နဲ့ သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ဘာသာပြန်
  4. ပြန်စစ်ပြီး ပြင်လို့ရ (တစ်ကြောင်းချင်း)
  5. edge-tts (my-MM-ThihaNeural) နဲ့ အသံထုတ် → အချိန်ကွက်အတိုင်း ချုံ့/ဖြန့်
  5b. (optional) အချိန်ကွက်ထဲ မဝင်တဲ့လိုင်း → Gemini နဲ့ အလိုအလျောက်တိုအောင်ပြင်
      → အသံပြန်ထုတ် (တစ်ကြိမ်သာ)
  6. ဗီဒီယိုအသစ်နဲ့ ပေါင်း → MP4 download + SRT download

Run:  streamlit run app.py
"""
import asyncio
import hashlib
import json
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
</style>"""


_card_ctx_stack = []


def _spidey_card_open(n, title):
    import streamlit as st
    # open/close ကို function နှစ်ခုနဲ့ ခွဲထားလို့ container ရဲ့
    # __enter__/__exit__ ကို ကိုယ်တိုင် မောင်းတာ — `with st.container():` နဲ့ အတူတူပဲ။
    # (ကြားထဲမှာ st.rerun/st.stop ဖြစ်ရင် run ပြတ်သွားမယ် — run အသစ်မှာ
    #  Streamlit က context_dg_stack ကို အစက ပြန် reset လုပ်ပြီးသားမို့
    #  ဒီမှာ ကျန်နေတဲ့ အဟောင်း ctx ကို လွှတ်ပစ်လိုက်ရုံပဲ)
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


def _spidey_steps(S, is_video):
    """အဆင့် ၆ ဆင့်ရဲ့ တိုးတက်မှုကို ပြတဲ့ tracker."""
    import streamlit as st
    labels = ["ဖိုင်တင်", "စာသားထုတ်", "ဘာသာပြန်", "စာစစ်", "အသံထုတ်", "Download"]
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
    skip = [False, not is_video, False, False, False, False]
    cur = next((i for i in range(6) if not done[i] and not skip[i]), None)
    parts = []
    for i, lab in enumerate(labels):
        if done[i]:
            cls, icon = "done", "✅"
        elif skip[i]:
            cls, icon = "skip", "⏭️"
        elif i == cur:
            cls, icon = "current", "🔴"
        else:
            cls, icon = "todo", "⭕"
        parts.append(
            f'<div class="spidey-step {cls}"><span class="n">{icon}</span>{i + 1}. {lab}</div>'
        )
    st.markdown('<div class="spidey-steps">' + "".join(parts) + "</div>",
                unsafe_allow_html=True)


GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"  # sub-translator မှာ အလုပ်ဖြစ်နေတဲ့ model
# Whisper က ဘာသာစကား auto-detect မှားတတ်လို့ (ဥပမာ English ကို Tamil လို့ ထင်တာ)
# သုံးသူ တိတိကျကျ ရွေးနိုင်အောင် — (ပြသမယ့်အမည်, Whisper code)
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
GEMINI_MODEL_DEFAULT = "gemini-3.5-flash-lite"   # Script-writer / sub-translator မှာ အလုပ်ဖြစ်နေတဲ့ model
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models/"
VOICE_MALE = "my-MM-ThihaNeural"
VOICE_FEMALE = "my-MM-NilarNeural"


# ------------------------------------------------------------------ helpers
def run(cmd):
    """ffmpeg/ffprobe စတာတွေ run ဖို့ (stderr ဖွက်)."""
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
def transcribe_audio(audio_path, api_key, language=None):
    """Groq Whisper API နဲ့ transcribe လုပ် → {'language':..., 'segments':[{'start','end','text'}]}.

    language: Whisper ISO code (ဥပမာ "en") — ပေးရင် auto-detect မလုပ်ဘဲ
    အဲ့ဘာသာစကားအတိုင်း နားထောင်မယ်။ None ဆို auto-detect (အရင်အတိုင်း)။

    sub-translator မှာ အလုပ်ဖြစ်နေတဲ့ request ပုံစံအတိုင်း
    (whisper-large-v3-turbo, verbose_json) — Streamlit Cloud RAM ကန့်သတ်ချက်ကြောင့်
    local faster-whisper အစား ဒီ API ကို သုံးထားတာ။
    """
    import requests  # local import
    size = os.path.getsize(audio_path)
    if size > 20 * 1024 * 1024:
        raise RuntimeError("အသံဖိုင် 20MB ကျော်နေတယ် — Groq က 25MB အထိပဲ လက်ခံတယ်။ "
                           "ဗီဒီယိုအတိုလေးနဲ့ စမ်းကြည့်ပါ။")
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
        raise RuntimeError(f"စာသားထုတ်တာ ပျက်သွားတယ်: {msg}")
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


# ------------------------------------------------------- step 3: translate
_TRANSLATE_SYS = (
    "You translate video subtitle lines for Myanmar voiceover dubbing. "
    "Translate each line into natural SPOKEN Burmese (Myanmar) — the way a narrator "
    "would say it out loud, not formal written style. Keep the meaning, keep it "
    "concise (it must fit the original speaking time). Do not add explanations. "
    "Return ONLY a JSON array of objects with keys 'id' and 'text'."
)


def _gemini_call(api_key, model_id, system_text, payload_text):
    import requests  # local import: requests မရှိရင် ဒီ step မှပဲ error တက်
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
    """sidebar glossary box → [(foreign, burmese), ...].

    ပုံစံ: တစ်ကြောင်းတစ်ခု၊ `John=ဂျွန်` — `=` မပါတာ/လွတ်နေတာတွေ ကျော်။
    """
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


def gemini_translate(api_key, segments, model_id, progress_cb=None, glossary=None):
    """segments: [{'start','end','text'}] → [{'start','end','src','text'}].

    ပြန်မရတဲ့ အပိုင်းတွေက မူရင်းစာသားအတိုင်း ကျန်ပြီး failed_ids မှာ မှတ်ထားတယ်။
    """
    items = [{"id": i, "text": s["text"]} for i, s in enumerate(segments)]
    out = {}
    failed = []
    _sys = _TRANSLATE_SYS + _glossary_prompt(glossary)
    BATCH = 25
    batches = [items[i:i + BATCH] for i in range(0, len(items), BATCH)]
    for b, batch in enumerate(batches):
        try:
            res = _gemini_call(api_key, model_id, _sys,
                               json.dumps(batch, ensure_ascii=False))
            for row in res:
                if isinstance(row, dict) and "id" in row and "text" in row:
                    out[int(row["id"])] = str(row["text"]).strip()
            missing = [x["id"] for x in batch if x["id"] not in out]
            failed.extend(missing)
        except Exception:
            failed.extend([x["id"] for x in batch])
        if progress_cb:
            progress_cb((b + 1) / len(batches))
    # ပြန်မရတာတွေ တစ်ကြိမ်ထပ်ကြိုးစား
    if failed:
        retry = [x for x in items if x["id"] in failed]
        still = []
        for b, batch in enumerate([retry[i:i + BATCH] for i in range(0, len(retry), BATCH)]):
            try:
                res = _gemini_call(api_key, model_id, _sys,
                                   json.dumps(batch, ensure_ascii=False))
                for row in res:
                    if isinstance(row, dict) and "id" in row and "text" in row:
                        out[int(row["id"])] = str(row["text"]).strip()
                        if int(row["id"]) in failed:
                            failed.remove(int(row["id"]))
            except Exception:
                still.extend([x["id"] for x in batch])
    result = []
    for i, s in enumerate(segments):
        result.append({"start": s["start"], "end": s["end"],
                       "src": s["text"], "text": out.get(i, s["text"])})
    return result, failed


def merge_tiny_segments(segments, max_gap=0.5, min_slot=1.5, max_merged=8.0):
    """Whisper (verbose_json) က တခါတလေ စက္ကန့်ပိုင်းအကွက်သေးသေးလေးတွေ
    (ဥပမာ 0.2s) ပေးတတ်တယ် — အဲ့ဒါတွေကို ကပ်နေတဲ့နောက်အပိုင်းနဲ့ ပေါင်းလိုက်.

    စည်း: အကွက်က min_slot ထက် သေးနေသေးရင် + နောက်အပိုင်းနဲ့ကြားက gap က
    max_gap ထက်နည်းရင် ပေါင်း; ပေါင်းပြီးသားအကွက် max_merged ထက် မကျော်စေနဲ့.
    စကားပြောရပ်တဲ့နေရာ (gap ကြီး) တွေတော့ မပေါင်းဘူး — sync မပျက်စေဖို့.
    """
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
                cur["src"] = ((cur.get("src") or "") + " "
                              + (nxt.get("src") or "")).strip()
            i += 1
        merged.append(cur)
        i += 1
    return merged


_SHORTEN_SYS = (
    "You rewrite subtitle lines SHORTER for voiceover dubbing. Each line will be "
    "spoken by TTS inside a tight time slot, so compress aggressively: cut filler "
    "words, drop repeated ideas, keep only the core meaning. Keep natural SPOKEN "
    "Burmese (Myanmar). Each item has 'max_chars' — stay under it if possible. "
    "Return ONLY a JSON array of objects with keys 'id' and 'text'."
)


def gemini_shorten(api_key, model_id, items, glossary=None):
    """items: [{'id': seg_idx, 'text':..., 'target_chars':...}]
    → {seg_idx: တိုထားတဲ့စာသား}. ပျက်ရင်/ပြန်မရရင် အဲ့အပိုင်း ပါမလာဘူး
    (မူရင်းအတိုင်း ကျန်မယ်)."""
    payload = [{"id": x["id"], "text": x["text"],
                "max_chars": x["target_chars"]} for x in items]
    try:
        res = _gemini_call(api_key, model_id,
                           _SHORTEN_SYS + _glossary_prompt(glossary),
                           json.dumps(payload, ensure_ascii=False))
    except Exception:
        return {}
    out = {}
    for row in res:
        if isinstance(row, dict) and "id" in row and "text" in row:
            t = str(row["text"]).strip()
            if t:
                out[int(row["id"])] = t
    return out


# ----------------------------- browser localStorage (key မပျောက်ဖို့)
_LS_GEMINI = "audiodub_gemini_key"
_LS_GROQ = "audiodub_groq_key"
_LS_GLOSSARY = "audiodub_glossary"


def _local_storage(st):
    """browser localStorage component — package မရှိရင်/ပျက်ရင် None."""
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
    # eraseItem = browser localStorage ကနေ တကယ်ဖျက် (deleteItem က value ပဲ reset);
    # memory ထဲက storedItems ကိုပါ ထုတ်
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
    """စာတစ်ကြောင်းကို TTS mp3 ထုတ် (cache ပါ). မရရင် None.

    မှတ်ချက်: ဒီစက်ရဲ့ network က Microsoft TTS ကို ပိတ်ထားလို့ ဒီမှာစမ်းရင်
    ပျက်မယ် — အဲ့တာ bug မဟုတ်ဘူး၊ user စက်မှာ အလုပ်လုပ်တယ်။
    """
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
    """TTS clip ကို အချိန်ကွက် (slot) ထဲ ထည့်.

    - သဘာဝအတိုင်း ဆန့်ရင် အတိုင်းထား (ကျန်တာ silence ဖြည့်)
    - နည်းနည်းရှည်ရင် max_speed (default 1.3x) အထိ မြန်ပေး
    - အဲ့မှာမှ မဆန့်ရင် max_speed နဲ့ နောက်က silence ငှားသုံး၊
      နောက်အပိုင်းနဲ့တော့ ဘယ်တော့မှ မထပ်စေနဲ့
    Returns: (played_duration, note, ratio)
    """
    d = dur(src_mp3)
    ratio = d / slot if slot > 0 else 1.0
    filters = []
    if ratio <= 1.0:
        # သဘာဝအတိုင်း ဆန့်တယ်: slot အပြည့် silence နဲ့ဖြည့် (timeline မရွေ့စေဖို့)
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
    """segments: [{'start','end','text'}] → fitted mp3 တွေ.

    Returns: (fitted=[(start, seg_path, played)], report={natural, sped,
             overflow:[...], tts_failed:[...]})
    """
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
    """fitted clip တွေကို timeline အတိုင်း ဆက် → total_duration အတိအကျ mp3."""
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
        # ပထမအပိုင်းမစခင် ဦးဆောင်တိတ်ဆိတ်မှု (timeline မရွေ့စေဖို့)
        if fitted and fitted[0][0] > 0.02:
            fh.write(f"file '{gap_file(fitted[0][0])}'\n")
        for j, (start, seg, played) in enumerate(fitted):
            fh.write(f"file '{seg}'\n")
            next_s = fitted[j + 1][0] if j + 1 < len(fitted) else total_duration
            gap = next_s - (start + played)
            if gap > 0.02:
                fh.write(f"file '{gap_file(gap)}'\n")
    # re-encode (MP3 frame padding က timeline မပျက်စေဖို့)
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", lst, "-c:a", "libmp3lame", "-b:a", "96k",
         "-ar", "24000", "-ac", "1", out_mp3])
    return out_mp3


def mux_video(video_path, dubbed_mp3, out_mp4):
    """မူရင်းဗီဒီယို (ပုံအတိုင်း) + အသံသစ် → MP4."""
    run(["ffmpeg", "-y", "-v", "error", "-i", video_path, "-i", dubbed_mp3,
         "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
         "-shortest", out_mp4])
    return out_mp4


def segments_to_srt(segments):
    lines = []
    for i, s in enumerate(segments, 1):
        lines.append(f"{i}\n{fmt_ts(s['start'])} --> {fmt_ts(s['end'])}\n{s['text']}\n")
    return "\n".join(lines)


_SRT_TS_LINE = re.compile(
    r"(\d+:[\d:.,]+)\s*-->\s*(\d+:[\d:.,]+)")


def parse_srt(text):
    """SRT ဖိုင်စာသား → [{start, end, text}]. စာသားအပိုဒ်များရင် space နဲ့ဆက်."""
    text = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    segs = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = [l for l in block.strip().split("\n") if l.strip()]
        if not lines:
            continue
        ts_idx = 0
        if "-->" not in lines[0] and len(lines) > 1:
            ts_idx = 1  # ပထမလိုင်းက နံပါတ်စဉ်
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


_REVIEW_LINE = re.compile(
    r"(\d+:\d+:[\d.,]+)\s*-->\s*(\d+:[\d:.,]+)\s*\|\s*(.*)")


def segments_to_review_text(segments):
    return "\n".join(f"{fmt_ts(s['start'])} --> {fmt_ts(s['end'])} | {s['text']}"
                     for s in segments)


def parse_review_text(raw):
    """ပြင်ပြီးသား text → segments. မှားနေတဲ့လိုင်း ရှိရင် error တက်."""
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


# မြန်မာစာမဟုတ်တဲ့ script တွေ (Tamil/Devanagari/Thai/Korean/CJK စသဖြင့်) —
# ဘာသာပြန်အမှား/အကြွင်းအကျန်တွေ ဖမ်းဖို့
_FOREIGN_SCRIPT_RE = re.compile(
    r"[\u0B80-\u0BFF\u0900-\u097F\u0E00-\u0E7F\u3040-\u30FF\uAC00-\uD7AF\u4E00-\u9FFF]")
# my-MM TTS ခန့်မှန်းအမြန်နှုန်း (စာလုံး/စက္ကန့်) — ပြဿနာလိုင်းရှာဖို့ ခန့်မှန်းချက်သက်သက်
_EST_CPS = 14.0


def find_problem_lines(segments, max_speed):
    """အဆင့် ၄ အတွက် ပြဿနာရှိနိုင်တဲ့လိုင်းတွေ ရှာပေး.

    → [(idx, "အကြောင်းရင်း"), ...]. TTS အစစ်မထုတ်ဘဲ ခန့်မှန်းချက်နဲ့ပဲ
    စစ်တာ (အတိအကျမဟုတ် — သတိပေးတဲ့သဘော).
    """
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
                reasons.append("မြန်မာမဟုတ်တဲ့ စာလုံး ပါနေတယ်")
            src = (s.get("src") or "").strip()
            if src and text == src and re.search(r"[A-Za-z]{3,}", text):
                reasons.append("ဘာသာမပြန်ရသေးဘူး (မူရင်းအတိုင်း ကျန်နေတယ်)")
        if reasons:
            flags.append((i, " + ".join(reasons)))
    return flags


def mix_ducked(video_path, voiceover_mp3, out_mp3):
    """မူရင်းအသံ (HQ) + dub အသံ → ducking နဲ့ ရော.

    စကားမပြောတဲ့အပိုင်း → မူရင်းအသံ (သီချင်း/SFX) အပြည့်၊
    dub အသံထွက်နေချိန် → sidechaincompress က မူရင်းအသံကို
    အလိုအလျောက် ဖိချမယ် (attack/release ကြောင့် ချောချောမွေ့မွေ့)။
    ဗီဒီယိုမှာ audio stream မရှိရင် None ပြန်မယ်။
    """
    # မူရင်းမှာ audio ရှိမရှိ စစ်
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a",
         "-show_entries", "stream=index", "-of", "csv=p=0", video_path],
        capture_output=True, text=True)
    if not r.stdout.strip():
        return None
    work = os.path.join(WORK_DIR, "ducktmp")
    os.makedirs(work, exist_ok=True)
    orig_hq = os.path.join(work, "orig_hq.mp3")
    run(["ffmpeg", "-y", "-v", "error", "-i", video_path, "-vn",
         "-ar", "44100", "-ac", "2", "-b:a", "128k", orig_hq])
    # NOTE: mono->stereo via aformat alone LOSES ~8dB on the voice (ffmpeg's
    # default upmix matrix attenuates). Use pan to duplicate mono c0 to both
    # stereo channels at full level instead. (assemble_dubbed always emits mono.)
    # NOTE 2: [key] feeds TWO filters -> must asplit first; reusing a pad
    # without asplit silently feeds silence to the second consumer (voice lost!).
    fc = (
        "[0:a]aformat=sample_fmts=fltp:sample_rates=44100:channel_layouts=stereo[orig];"
        "[1:a]pan=stereo|c0=c0|c1=c0,aresample=44100,aformat=sample_fmts=fltp,asplit=2[k1][k2];"
        "[orig][k1]sidechaincompress=threshold=0.05:ratio=8:attack=250:release=600[d];"
        "[d][k2]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[m];"
        "[m]alimiter=limit=0.95,aresample=44100,aformat=channel_layouts=stereo[out]"
    )
    run(["ffmpeg", "-y", "-v", "error", "-i", orig_hq, "-i", voiceover_mp3,
         "-filter_complex", fc, "-map", "[out]",
         "-c:a", "libmp3lame", "-b:a", "128k", out_mp3])
    return out_mp3


def _reset_review_keys(S):
    """ဘာသာပြန် အသစ်ရတိုင်း review textarea + quick-fix key တွေ ရှင်း
    (အဟောင်း widget state က စာအသစ်ကို မဖုံးစေဖို့)."""
    if "review_text" in S:
        del S["review_text"]
    for k in [k for k in S.keys() if k.startswith("fixline_")]:
        del S[k]


# ------------------------------------------------------------------ UI
def _init_state(st):
    defaults = {
        "run_id": None, "video_path": None, "audio_path": None, "duration": 0.0,
        "src_segments": None, "translations": None, "final_segments": None,
        "fitted": None, "fit_report": None, "out_mp4": None, "out_mp3": None,
        "lang": "", "auto_shortened": False,
        "srt_name": "", "srt_is_my": False, "dl_base": "",
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
        st.caption("Key တွေ၊ အသံနဲ့ ရွေးချယ်စရာတွေ ဒီမှာပြင်")
        st.markdown("#### 🔑 API Keys")
        localS = _local_storage(st)
        # key ဖျက်တာ — widget တွေ မပေါ်ခင် (run အစ) မှာ လုပ်
        if S.get("_clear_keys"):
            _ls_del(localS, _LS_GEMINI, "ls_del_gemini")
            _ls_del(localS, _LS_GROQ, "ls_del_groq")
            for _k in ("gemini_key", "groq_key"):
                if _k in S:
                    del S[_k]
            del S["_clear_keys"]
        # --- Gemini key: server secret > ရိုက်ထည့်ထား > browser သိမ်းထား ---
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if not env_key and "gemini_key" not in S:
            _sg = _ls_get(localS, _LS_GEMINI)
            if _sg:
                S["gemini_key"] = _sg
        key_input = st.text_input("Gemini API Key", type="password", key="gemini_key",
                                  placeholder="AIzaSy...",
                                  help="စာသားဘာသာပြန်ဖို့သုံး — တစ်ခါထည့်ထားရင် browser မှာ "
                                       "မှတ်ထားမယ်၊ hard refresh ဆွဲလည်း မပျောက်ဘူး")
        typed_gemini = key_input.strip()
        if typed_gemini and typed_gemini != _ls_get(localS, _LS_GEMINI):
            _ls_set(localS, _LS_GEMINI, typed_gemini, "ls_set_gemini")
        api_key = typed_gemini or env_key
        if api_key:
            st.success("✅ Gemini key ရှိတယ်")
        else:
            st.warning("⚠️ Gemini key မရှိသေးဘူး (အဆင့် ၃ အတွက်လိုတယ်)")
        # --- Groq key: server secret > ရိုက်ထည့်ထား > browser သိမ်းထား ---
        env_groq = os.environ.get("GROQ_API_KEY", "").strip()
        if not env_groq and "groq_key" not in S:
            _sq = _ls_get(localS, _LS_GROQ)
            if _sq:
                S["groq_key"] = _sq
        groq_input = st.text_input("Groq API Key", type="password", key="groq_key",
                                   placeholder="gsk_...",
                                   help="အသံမှ စာသားထုတ်ဖို့သုံး — console.groq.com မှာ အလကားယူလို့ရ။ "
                                        "တစ်ခါထည့်ထားရင် browser မှာ မှတ်ထားမယ်")
        typed_groq = groq_input.strip()
        if typed_groq and typed_groq != _ls_get(localS, _LS_GROQ):
            _ls_set(localS, _LS_GROQ, typed_groq, "ls_set_groq")
        groq_key = typed_groq or env_groq
        if groq_key:
            st.success("✅ Groq key ရှိတယ်")
        else:
            st.warning("⚠️ Groq key မရှိသေးဘူး (အဆင့် ၂ အတွက်လိုတယ်)")
        # glossary: browser သိမ်းထားတာ ရှိရင် ပြန် load
        if "glossary" not in S:
            _gg = _ls_get(localS, _LS_GLOSSARY)
            if _gg:
                S["glossary"] = _gg
        if st.button("🔑 သိမ်းထားတဲ့ key တွေ ဖျက်",
                     help="browser မှာ မှတ်ထားတဲ့ key တွေကို ဖျက်မယ် "
                          "(ဥပမာ သူများဖုန်း/ကွန်ပျူတာနဲ့ သုံးပြီးရင်)"):
            S["_clear_keys"] = True
            st.rerun()
        st.divider()
        st.markdown("#### 🎚️ အသံ ဆက်တင်")
        model_id = st.text_input("Gemini model", value=GEMINI_MODEL_DEFAULT)
        max_speed = st.slider("အမြန်ဆုံးနှုန်း (အသံချုံ့တာ)", 1.0, 2.0, 1.3, 0.05,
                              help="စာရှည်ရင် ဒီနှုန်းအထိ မြန်ပေးမယ်")
        voice = st.selectbox("အသံ", [VOICE_MALE, VOICE_FEMALE],
                             format_func=lambda v: "🗣️ ကျား (Thiha)" if v == VOICE_MALE else "🗣️ မ (Nilar)")
        if st.button("🔊 အသံ စမ်းနားထောင်ရန်", use_container_width=True,
                     help="ရွေးထားတဲ့အသံနဲ့ နမူနာစာတစ်ကြောင်း ဖတ်ပြမယ် — "
                          "အဆင့် ၅ မလုပ်ခင် အသံကြိုက်မကြိုက် စစ်လို့ရတယ်"):
            _sample = "မင်္ဂလာပါ။ ဒီအသံနဲ့ ဇာတ်လမ်းကို ပြောပြမယ်။"
            with st.spinner("အသံထုတ်နေတယ်..."):
                _tp = tts_segment(_sample, voice, VOICE_FEMALE)
            if _tp:
                S["_voice_test"] = _tp
            else:
                st.error("အသံထုတ်မရဘူး — network / VPN စစ်ပါ")
        if S.get("_voice_test") and os.path.isfile(S["_voice_test"]):
            st.audio(S["_voice_test"])
        st.divider()
        st.markdown("#### ⚙️ ရွေးချယ်စရာ")
        auto_merge = st.checkbox("🔗 အပိုင်းသေးတွေ အလိုအလျောက်ပေါင်း", value=True,
                                 help="Whisper ပေးတဲ့ စက္ကန့်ပိုင်းအကွက်သေးလေးတွေကို "
                                      "ကပ်နေတဲ့အပိုင်းနဲ့ ပေါင်းမယ် — အသံအရမ်းမြန်ရတာသက်သာမယ်။ "
                                      "ပိတ်ထားရင် အရင်အတိုင်း")
        auto_shorten = st.checkbox("✂️ စာရှည်ရင် Gemini နဲ့ အလိုအလျောက်တိုပေး", value=True,
                                   help="အချိန်ကွက်ထဲ မဝင်တဲ့လိုင်းတွေကို Gemini က တိုတိုပြန်ရေးပြီး "
                                        "အသံပြန်ထုတ်မယ် (တစ်ကြိမ်သာ)။ ပိတ်ထားရင် အရင်အတိုင်း")
        keep_bg = st.checkbox("🎵 နောက်ခံအသံ ချန်ထား (ducking)", value=True,
                              help="စကားမပြောတဲ့အပိုင်း → မူရင်းအသံ (သီချင်း/SFX) အပြည့်; "
                                   "dub အသံထွက်နေချိန် → မူရင်းအသံ အလိုအလျောက် တိုးသွားမယ်။ "
                                   "ဗီဒီယိုမုဒ်အတွက်သာ။ ပိတ်ထားရင် အရင်အတိုင်း (dub အသံသက်သက်)")
        st.markdown("##### 📖 နာမည်စာရင်း (Glossary)")
        glossary_raw = st.text_area(
            "ဇာတ်ကောင်နာမည်တွေ — တစ်ကြောင်းတစ်ခု",
            key="glossary", height=90, placeholder="John=ဂျွန်\nSarah=ဆာရာ",
            help="ဘာသာပြန်တိုင်း ဒီနာမည်တွေကို ဒီမြန်မာလိုအတိုင်း သုံးမယ် — "
                 "Gemini က တစ်မျိုးတစ်မျိုး ပြောင်းပြန်မှာ စိုးလို့။ browser မှာ မှတ်ထားမယ်")
        _g_stored = _ls_get(localS, _LS_GLOSSARY)
        if glossary_raw.strip() != _g_stored:
            if glossary_raw.strip():
                _ls_set(localS, _LS_GLOSSARY, glossary_raw.strip(), "ls_set_glossary")
            else:
                _ls_del(localS, _LS_GLOSSARY, "ls_del_glossary")
        glossary = parse_glossary(glossary_raw)
        if glossary:
            st.caption(f"✅ {len(glossary)} ခု မှတ်ထားပြီးပြီ")
        st.divider()
        st.markdown("#### 🗑️ အသစ်")
        if st.button("အစက ပြန်စ", use_container_width=True):
            for k in list(S.keys()):
                del S[k]
            st.rerun()

    # ---------------------------------------------------------- main
    st.markdown(
        '<div class="spidey-hero">'
        '<div class="spidey-kicker">🕸️ FRIENDLY NEIGHBORHOOD DUBBING 🕸️</div>'
        '<div class="spidey-title">Audio Dub Studio</div>'
        '<div class="spidey-sub">ဗီဒီယို / SRT → မြန်မာအသံ — မူရင်းအချိန်အတိုင်း 🕷️</div>'
        "</div>",
        unsafe_allow_html=True,
    )

    mode = st.radio("အရင်းအမြစ်", ["🎬 ဗီဒီယို", "📄 SRT ဖိုင်"], horizontal=True,
                    key="src_mode",
                    help="ဗီဒီယိုတင်ပြီး အစအဆုံးလုပ်မလား၊ "
                         "SRT ဖိုင်အဆင်သင့်ရှိလို့ အဲ့ဒါကနေပဲ ဆက်လုပ်မလား")
    if S.get("_mode") is not None and S["_mode"] != mode:
        for k in ("run_id", "video_path", "audio_path", "duration",
                  "src_segments", "translations", "final_segments",
                  "fitted", "fit_report", "out_mp4", "out_mp3", "lang",
                  "auto_shortened", "srt_name", "srt_is_my", "dl_base",
                  "dl_name", "_dl_for"):
            if k in S:
                del S[k]
        _reset_review_keys(S)
        S["_mode"] = mode
        st.rerun()
    S["_mode"] = mode
    is_video = (mode == "🎬 ဗီဒီယို")
    _spidey_steps(S, is_video)

    # ---- အဆင့် ၁: upload (ဗီဒီယို / SRT)
    _spidey_card_open(1, "ဗီဒီယိုတင်ပါ" if is_video else "SRT ဖိုင်တင်ပါ")
    if is_video:
        up = st.file_uploader("MP4 / MOV / WEBM ဖိုင်ရွေးပါ", type=["mp4", "mov", "webm"])
        if S.video_path:
            st.info(f"📁 {os.path.basename(S.video_path)} — {S.duration:.1f} စက္ကန့်")
        _bc1, _ = st.columns([1, 2])
        with _bc1:
            _go1 = (st.button("▶️ အသံထုတ်ယူရန်", type="primary",
                              use_container_width=True)
                    if up is not None else False)
        if _go1:
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
            st.success(f"✅ အသံထုတ်ပြီးပြီ — ဗီဒီယို {d:.1f} စက္ကန့်")
            st.rerun()
    else:
        srt_up = st.file_uploader("SRT ဖိုင်ရွေးပါ", type=["srt"], key="srt_up")
        srt_lang_choice = st.radio(
            "SRT က ဘယ်ဘာသာစကားလဲ",
            ["🌐 ဘာသာခြား (ဘာသာပြန်မယ်)", "✅ မြန်မာလို အဆင်သင့် (တိုက်ရိုက်အသံထုတ်မယ်)"],
            horizontal=True, key="srt_lang_radio")
        is_my = srt_lang_choice.startswith("✅")
        if S.src_segments:
            st.info(f"📄 {S.srt_name} — အပိုင်း {len(S.src_segments)} ခု")
        _bc1s, _ = st.columns([1, 2])
        with _bc1s:
            _gos = (st.button("▶️ SRT ဖတ်ရန်", type="primary",
                              use_container_width=True)
                    if srt_up is not None else False)
        if _gos:
            raw = srt_up.getbuffer()
            text = None
            for enc in ("utf-8-sig", "utf-16", "cp1252"):
                try:
                    text = bytes(raw).decode(enc)
                    break
                except (UnicodeDecodeError, ValueError):
                    continue
            segs = parse_srt(text or "")
            if not segs:
                st.error("SRT ထဲမှာ စာသားမတွေ့ဘူး — ဖိုင်စစ်ကြည့်ပါ")
                st.stop()
            run_id = uuid.uuid4().hex[:8]
            rd = os.path.join(WORK_DIR, run_id)
            os.makedirs(rd, exist_ok=True)
            S.update(run_id=run_id, video_path=None, audio_path=None,
                     duration=segs[-1]["end"],
                     src_segments=segs, lang="",
                     translations=None, final_segments=None,
                     fitted=None, fit_report=None, out_mp4=None, out_mp3=None,
                     srt_name=srt_up.name, srt_is_my=is_my,
                     dl_base=os.path.splitext(srt_up.name)[0])
            if is_my:
                # မြန်မာလို အဆင်သင့်မို့ ဘာသာပြန်စရာမလို — အဆင့် ၄ တန်းသွား
                S.translations = [{"start": s["start"], "end": s["end"],
                                   "text": s["text"], "src": ""} for s in segs]
            _reset_review_keys(S)
            st.success(f"✅ SRT ဖတ်ပြီးပြီ — အပိုင်း {len(segs)} ခု")
            st.rerun()
    _spidey_card_close()

    # ---- အဆင့် ၂: transcribe (ဗီဒီယိုမုဒ်သာ)
    _spidey_card_open(2, "အသံမှ စာသားထုတ်")
    if not is_video:
        st.info("📄 SRT ဖိုင်ကနေ တိုက်ရိုက်ရပြီးမို့ ဒီအဆင့်မလိုဘူး — အဆင့် ၃ ကို ဆက်သွားပါ။")
    elif not S.audio_path:
        st.caption("အရင်ဆုံး အဆင့် ၁ မှာ ဗီဒီယိုတင်ပါ။")
    elif not groq_key:
        st.warning("⚠️ Groq API Key ထည့်မှ စာသားထုတ်လို့ရမယ် (ဘယ်ဘက် sidebar)။")
    else:
        _lang_label = st.selectbox(
            "🎙️ မူရင်းဘာသာစကား",
            [lbl for lbl, _ in _SRC_LANGS], key="src_lang",
            help="Whisper က ဘာသာစကား မှားသိတတ်တယ် (ဥပမာ English အသံကို "
                 "Tamil စာနဲ့ ရေးချတာ) — ဗီဒီယိုက ဘာဘာသာစကားလဲ သိရင် "
                 "ဒီမှာ တိတိကျကျ ရွေးလိုက်။ မသိရင် Auto ထားခဲ့။")
        _lang_code = dict(_SRC_LANGS)[_lang_label]
        _bc2, _ = st.columns([1, 2])
        with _bc2:
            _go2 = st.button("🎤 နားထောင်ပြီး စာသားထုတ်ရန်", type="primary",
                             use_container_width=True)
        if _go2:
            with st.status("Groq Whisper API နဲ့ နားထောင်နေတယ်...", expanded=True) as stt:
                try:
                    data = transcribe_audio(S.audio_path, groq_key,
                                            language=_lang_code)
                except Exception as e:
                    stt.update(state="error")
                    st.error(str(e))
                    st.stop()
            segs = [{"start": x["start"], "end": x["end"], "text": x["text"]}
                    for x in data.get("segments", [])]
            merge_note = ""
            if auto_merge:
                before = len(segs)
                segs = merge_tiny_segments(segs)
                if len(segs) < before:
                    merge_note = f" (အပိုင်းသေး {before - len(segs)} ခု ပေါင်းပြီးပြီ)"
            S.src_segments, S.lang = segs, data.get("language", "")
            S.translations, S.final_segments, S.fitted = None, None, None
            stt.update(state="complete")
            st.success(f"✅ အပိုင်း {len(segs)} ခု တွေ့တယ်{merge_note}"
                       + (f" (ဘာသာစကား: {S.lang})" if S.lang else ""))
        if S.src_segments:
            with st.expander(f"တွေ့တဲ့အပိုင်း {len(S.src_segments)} ခု ကြည့်"):
                for s in S.src_segments[:50]:
                    st.write(f"`{fmt_ts(s['start'])} → {fmt_ts(s['end'])}` {s['text']}")
                if len(S.src_segments) > 50:
                    st.caption(f"...နောက် {len(S.src_segments) - 50} ခု ကျန်သေးတယ်")

    _spidey_card_close()

    # ---- အဆင့် ၃: translate
    _spidey_card_open(3, "မြန်မာလို ဘာသာပြန်")
    if not S.src_segments:
        st.caption("အရင်ဆုံး အဆင့် ၁ မှာ " +
                   ("ဗီဒီယိုတင်" if is_video else "SRT ဖိုင်တင်") + "ပါ။")
    elif S.get("srt_is_my"):
        st.info("✅ SRT က မြန်မာလိုအဆင်သင့်မို့ ဘာသာပြန်စရာမလိုဘူး — "
                "အဆင့် ၄ ကို ဆက်သွားပါ။")
        if S.translations:
            with st.expander("SRT စာသား ကြည့်"):
                for s in S.translations[:30]:
                    st.write(f"`{fmt_ts(s['start'])}` {s['text']}")
    elif not api_key:
        st.warning("⚠️ Gemini API key ထည့်မှ ဘာသာပြန်လို့ရမယ် (ဘယ်ဘက် sidebar)။")
    else:
        _bc3, _ = st.columns([1, 2])
        with _bc3:
            _go3 = st.button("🌐 သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ပြန်ရန်",
                             type="primary", use_container_width=True)
        if _go3:
            prog = st.progress(0.0, "Gemini နဲ့ ဘာသာပြန်နေတယ်...")
            try:
                result, failed = gemini_translate(
                    api_key, S.src_segments, model_id.strip() or GEMINI_MODEL_DEFAULT,
                    progress_cb=lambda f: prog.progress(f), glossary=glossary)
            except Exception as e:
                st.error(f"ဘာသာပြန်တာ ပျက်သွားတယ်: {e}")
                st.stop()
            S.translations, S.final_segments, S.fitted = result, None, None
            _reset_review_keys(S)
            prog.empty()
            if failed:
                st.warning(f"⚠️ {len(failed)} ပိုင်း ပြန်မရလို့ မူရင်းစာသားအတိုင်း ထားထားတယ်")
            st.success(f"✅ {len(result)} ပိုင်း ဘာသာပြန်ပြီးပြီ")
        if S.translations:
            with st.expander("ဘာသာပြန်ချက် ကြည့်"):
                for s in S.translations[:30]:
                    st.write(f"`{fmt_ts(s['start'])}` {s['text']}")
                    st.caption(f"မူရင်း: {s['src'][:80]}")

    _spidey_card_close()

    # ---- အဆင့် ၄: review / edit
    _spidey_card_open(4, "စာသားစစ် / ပြင်")
    if not S.translations:
        st.caption("အရင်ဆုံး အဆင့် ၃ မှာ ဘာသာပြန်ပါ။")
    else:
        # 🔍 ပြဿနာလိုင်းရှာသူ — textarea မပေါ်ခင် အရင်စစ်တာ:
        # ဒီအစဉ်လိုက်ထားမှ quick-fix က textarea�ဲ ဒီတစ်ပတ်တည်း တိုက်ရိုက်ရေးလို့ရမယ်
        # (widget ပေါ်ပြီးမှ session_state ပြင်ရင် Streamlit က error ထုတ်လို့)
        _cur_raw = S.get("review_text")
        if _cur_raw is None:
            _cur_raw = segments_to_review_text(S.translations)
        try:
            _work = parse_review_text(_cur_raw)
            _parse_ok = True
        except ValueError:
            _work = S.translations
            _parse_ok = False
        _flags = find_problem_lines(_work, max_speed)
        if _flags:
            with st.expander(
                    f"🔍 ပြဿနာရှိနိုင်တဲ့လိုင်းများ ({len(_flags)})", expanded=False):
                st.caption("တစ်ခုချင်းနှိပ်ပြင်ရုံနဲ့ အောက်ကစာထဲ သူ့အလိုလို ဝင်သွားမယ်")
                if not _parse_ok:
                    st.warning("အောက်ကစာမှာ ပုံစံမှားနေလို့ ဒီမှာ တိုက်ရိုက်ပြင်မရဘူး — "
                               "အရင်ပြင်လိုက်ပါ")
                for (i, _reason) in _flags:
                    _s = _work[i]
                    _fk = f"fixline_{S.run_id}_{i}"
                    _new = st.text_input(
                        f"#{i + 1} `{fmt_ts(_s['start'])} → {fmt_ts(_s['end'])}` — {_reason}",
                        value=_s["text"], key=_fk, disabled=not _parse_ok)
                    if _parse_ok and _new != _s["text"]:
                        _work[i]["text"] = _new
                        S["review_text"] = segments_to_review_text(_work)
                        st.rerun()  # flag စာရင်း ပြန်တွက်ဖို့
        raw = st.text_area(
            "တစ်ကြောင်းချင်း ပြင်လို့ရတယ် — အစဉ်မပြောင်းနဲ့၊ ပုံစံမဖျက်နဲ့",
            value=segments_to_review_text(S.translations), height=300,
            key="review_text")
        _bc4, _ = st.columns([1, 2])
        with _bc4:
            _go4 = st.button("✔️ စစ်ပြီး ဆက်ရန်", type="primary",
                             use_container_width=True)
        if _go4:
            try:
                S.final_segments = parse_review_text(raw)
                S.fitted, S.out_mp4, S.out_mp3 = None, None, None
                st.success(f"✅ {len(S.final_segments)} ပိုင်း အတည်ပြုပြီးပြီ")
            except ValueError as e:
                st.error(str(e))

    _spidey_card_close()

    # ---- အဆင့် ၅: TTS + fit
    _spidey_card_open(5, "မြန်မာအသံထုတ် + အချိန်ချိန်")
    if not S.final_segments:
        st.caption("အရင်ဆုံး အဆင့် ၄ မှာ စာသားအတည်ပြုပါ။")
    else:
        st.caption("အသံတစ်ကြောင်းချင်းကို သူ့အချိန်ကွက်ထဲ အတိအကျထည့်မယ် — "
                   f"ရှည်ရင် {max_speed}x အထိ မြန်ပေးမယ်၊ နောက်အပိုင်းနဲ့ ဘယ်တော့မှ မထပ်စေဘူး။")
        _bc5, _ = st.columns([1, 2])
        with _bc5:
            _go5 = st.button("🔊 အသံထုတ်ရန်", type="primary",
                             use_container_width=True)
        if _go5:
            work_segs = os.path.join(WORK_DIR, S.run_id, "segs")
            prog = st.progress(0.0)
            curlbl = st.empty()
            def cb(f, i, t):
                prog.progress(f)
                curlbl.text(f"အပိုင်း {i + 1}/{len(S.final_segments)}: {t}")
            S.auto_shortened = False
            fitted, report = tts_and_fit(S.final_segments, voice, max_speed,
                                         work_segs, progress_cb=cb)
            # စာရှည်လို့ အချိန်ကွက်ထဲ မဝင်တဲ့လိုင်းတွေ → Gemini နဲ့ အလိုအလျောက်တိုပေး
            if auto_shorten and report["overflow"] and api_key:
                items = [{"id": i, "text": t,
                          "target_chars": max(4, int(len(t) / ratio * 1.15))}
                         for (i, _s, _e, t, ratio) in report["overflow"]]
                with st.status("✂️ Gemini နဲ့ စာရှည်တဲ့လိုင်းတွေ တိုအောင်ပြင်နေတယ်...",
                               expanded=False):
                    short = gemini_shorten(api_key,
                                           model_id.strip() or GEMINI_MODEL_DEFAULT,
                                           items, glossary=glossary)
                applied = 0
                for (i, _s, _e, t, _r) in report["overflow"]:
                    if i in short and short[i] != t:
                        S.final_segments[i]["text"] = short[i]
                        applied += 1
                if applied:
                    # တိုထားတဲ့စာသားနဲ့ အသံပြန်ထုတ် (တစ်ကြိမ်သာ — cache ကြောင့်
                    # မပြောင်းတဲ့လိုင်းတွေ အသံပြန်ထုတ်စရာ မလိုဘူး)
                    fitted, report = tts_and_fit(S.final_segments, voice, max_speed,
                                                 work_segs, progress_cb=cb)
                    S.auto_shortened = True
                    st.info(f"✂️ Gemini က {applied} လိုင်း တိုအောင်ပြင်ပြီးပြီ — "
                            "အသံပြန်ထုတ်ထားတယ်")
            S.fitted, S.fit_report, S.out_mp4, S.out_mp3 = fitted, report, None, None
            prog.empty(); curlbl.empty()
            st.success(f"✅ အပိုင်း {len(fitted)} ပိုင်း အသံထွက်ပြီးပြီ")
        if S.fit_report:
            r = S.fit_report
            st.info(f"သဘာဝအတိုင်း: {r['natural']} ပိုင်း | "
                    f"မြန်ပေးထားတာ (≤{max_speed}x): {r['sped']} ပိုင်း | "
                    f"အသံထုတ်မရတာ: {len(r['tts_failed'])} ပိုင်း")
            if r["overflow"]:
                auto_note = (" (Gemini နဲ့ အလိုအလျောက်တိုပြီးသား — "
                             "လက်နဲ့ထပ်တိုဖို့လိုနေသေးတယ်)" if S.auto_shortened else "")
                st.warning("⚠️ အောက်ပါလိုင်းတွေ ရှည်လွန်းနေတယ်" + auto_note + " — "
                           "အဆင့် ၄ မှာ တိုအောင်ပြင်ပြီး ပြန်လုပ်ပါ:")
                for i, s_, e_, t_, ratio in r["overflow"]:
                    st.write(f"#{i + 1} `{fmt_ts(s_)} → {fmt_ts(e_)}` "
                             f"(x{ratio:.2f} လိုတယ်): {t_[:80]}")
            if r["tts_failed"]:
                st.error("🔇 အသံထုတ်မရတဲ့အပိုင်းတွေ (တိတ်ဆိတ်အဖြစ်ကျန်မယ်) — "
                         "network / VPN စစ်ပါ:")
                for i, s_, t_ in r["tts_failed"]:
                    st.write(f"#{i + 1} `{fmt_ts(s_)}`: {t_}")

    _spidey_card_close()

    # ---- အဆင့် ၆: assemble + download
    _spidey_card_open(6, "ဗီဒီယိုနဲ့ပေါင်း + Download"
                      if is_video else "အသံဖိုင် Download")
    if not S.fitted:
        st.caption("အရင်ဆုံး အဆင့် ၅ မှာ အသံထုတ်ပါ။")
    else:
        if is_video:
            _bc6, _ = st.columns([1, 2])
            with _bc6:
                _go6 = st.button("🎬 မူရင်းဗီဒီယိုနဲ့ ပေါင်းရန်", type="primary",
                                 use_container_width=True)
            if _go6:
                work_asm = os.path.join(WORK_DIR, S.run_id, "asm")
                dubbed = os.path.join(WORK_DIR, S.run_id, "dubbed_audio.mp3")
                out = os.path.join(WORK_DIR, S.run_id, "dubbed_video.mp4")
                with st.status("အသံဆက် + ဗီဒီယိုနဲ့ပေါင်းနေတယ်...", expanded=False):
                    assemble_dubbed(S.fitted, S.duration, work_asm, dubbed)
                    _final_audio = dubbed
                    if keep_bg:
                        _mixed = os.path.join(WORK_DIR, S.run_id, "dubbed_mixed.mp3")
                        try:
                            if mix_ducked(S.video_path, dubbed, _mixed):
                                _final_audio = _mixed
                                st.info("🎵 နောက်ခံအသံ (သီချင်း/SFX) ချန်ထားပြီး "
                                        "dub အသံနဲ့ ရောထားတယ်")
                            else:
                                st.caption("မူရင်းဗီဒီယိုမှာ အသံလမ်းမရှိလို့ "
                                           "dub အသံသက်သက် သုံးထားတယ်")
                        except Exception as e:
                            st.warning("ducking မအောင်မြင်လို့ dub အသံသက်သက် "
                                       f"သုံးထားတယ်: {e}")
                    mux_video(S.video_path, _final_audio, out)
                S.out_mp4 = out
                st.success("✅ ပြီးပြီ! အောက်မှာ download ချလို့ရပြီ")
        else:
            _bc6s, _ = st.columns([1, 2])
            with _bc6s:
                _go6s = st.button("🎧 အသံဖိုင်ထုတ်ရန်", type="primary",
                                  use_container_width=True)
            if _go6s:
                work_asm = os.path.join(WORK_DIR, S.run_id, "asm")
                out = os.path.join(WORK_DIR, S.run_id, "dubbed_voiceover.mp3")
                with st.status("အသံဆက်နေတယ်...", expanded=False):
                    assemble_dubbed(S.fitted, S.duration, work_asm, out)
                S.out_mp3 = out
                st.success("✅ ပြီးပြီ! အောက်မှာ download ချလို့ရပြီ")
        _has_out = ((S.out_mp4 and os.path.isfile(S.out_mp4)) or
                    (S.out_mp3 and os.path.isfile(S.out_mp3)))
        if _has_out or S.final_segments:
            # ဖိုင်အသစ်တင်တိုင်း အမည်အကြံကို refresh (ရိုက်ထားတာကို မဖျက်)
            if S.get("_dl_for") != S.run_id:
                _base = (S.get("dl_base") or "audio").strip() or "audio"
                S["dl_name"] = f"{_base}_dubbed"
                S["_dl_for"] = S.run_id
            st.text_input("📝 ဖိုင်နာမည်", key="dl_name",
                          help="download ချမယ့်အမည် — .mp4/.mp3/.srt ကို သူ့အလိုလို ထည့်ပေးမယ်")
            _dl = re.sub(r'[\\/:*?"<>|]', "_", (S.get("dl_name") or "").strip())
            if not _dl:
                _dl = "dubbed"
        st.markdown('<div class="spidey-dl-label">📥 ရလာဒ်များ</div>',
                    unsafe_allow_html=True)
        _dc = st.columns(3)
        _di = 0
        if S.out_mp4 and os.path.isfile(S.out_mp4):
            with _dc[_di], open(S.out_mp4, "rb") as f:
                st.download_button("⬇️ Dubbed MP4", f, file_name=f"{_dl}.mp4",
                                   mime="video/mp4", type="primary",
                                   use_container_width=True)
            _di += 1
        if S.out_mp3 and os.path.isfile(S.out_mp3):
            with _dc[_di], open(S.out_mp3, "rb") as f:
                st.download_button("⬇️ Dubbed MP3", f, file_name=f"{_dl}.mp3",
                                   mime="audio/mpeg", type="primary",
                                   use_container_width=True)
            _di += 1
        if S.final_segments:
            with _dc[_di]:
                st.download_button("⬇️ SRT", segments_to_srt(S.final_segments),
                                   file_name=f"{_dl}.srt", mime="text/plain",
                                   use_container_width=True)
    _spidey_card_close()
    st.markdown(
        '<div class="spidey-foot">🕷️ Audio Dub Studio — '
        "your friendly neighborhood dubbing tool 🕸️</div>",
        unsafe_allow_html=True)


if __name__ == "__main__":
    main()

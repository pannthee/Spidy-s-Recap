#!/usr/bin/env python3
"""Audio Dub Studio — ဗီဒီယိုထဲက စာသားပြောအပိုင်းတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးတဲ့ tool.

RecapKit ရဲ့ Audio Dub feature ကို တစ်ယောက်စာသုံးဖို့ ပြန်ဆောက်ထားတာ။
Login မလို၊ ငွေမလို — ကိုယ့် Streamlit Cloud မှာ run တယ်။

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

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3-turbo"  # sub-translator မှာ အလုပ်ဖြစ်နေတဲ့ model
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
def transcribe_audio(audio_path, api_key):
    """Groq Whisper API နဲ့ transcribe လုပ် → {'language':..., 'segments':[{'start','end','text'}]}.

    sub-translator မှာ အလုပ်ဖြစ်နေတဲ့ request ပုံစံအတိုင်း (whisper-large-v3-turbo,
    verbose_json). Streamlit Cloud RAM ကန့်သတ်ချက်ကြောင့် local faster-whisper
    အစား ဒီ API ကို သုံးထားတာ — အောက်က code တွေထိစရာမလိုဘူး။
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


def gemini_translate(api_key, segments, model_id, progress_cb=None):
    """segments: [{'start','end','text'}] → [{'start','end','src','text'}].

    ပြန်မရတဲ့ အပိုင်းတွေက မူရင်းစာသားအတိုင်း ကျန်ပြီး failed_ids မှာ မှတ်ထားတယ်။
    """
    items = [{"id": i, "text": s["text"]} for i, s in enumerate(segments)]
    out = {}
    failed = []
    BATCH = 25
    batches = [items[i:i + BATCH] for i in range(0, len(items), BATCH)]
    for b, batch in enumerate(batches):
        try:
            res = _gemini_call(api_key, model_id, _TRANSLATE_SYS,
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
                res = _gemini_call(api_key, model_id, _TRANSLATE_SYS,
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


def gemini_shorten(api_key, model_id, items):
    """items: [{'id': seg_idx, 'text':..., 'target_chars':...}]
    → {seg_idx: တိုထားတဲ့စာသား}. ပျက်ရင်/ပြန်မရရင် အဲ့အပိုင်း ပါမလာဘူး
    (မူရင်းအတိုင်း ကျန်မယ်)."""
    payload = [{"id": x["id"], "text": x["text"],
                "max_chars": x["target_chars"]} for x in items]
    try:
        res = _gemini_call(api_key, model_id, _SHORTEN_SYS,
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


# ------------------------------------------------------------------ UI
def _init_state(st):
    defaults = {
        "run_id": None, "video_path": None, "audio_path": None, "duration": 0.0,
        "src_segments": None, "translations": None, "final_segments": None,
        "fitted": None, "fit_report": None, "out_mp4": None, "lang": "",
        "auto_shortened": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def main():
    import streamlit as st
    st.set_page_config(page_title="Audio Dub Studio", page_icon="🎙️", layout="wide")
    _init_state(st)
    S = st.session_state

    # ---------------------------------------------------------- sidebar
    with st.sidebar:
        st.header("⚙️ ဆက်တင်")
        key_input = st.text_input("Gemini API Key", type="password",
                                  placeholder="AIzaSy...", help="စာသားဘာသာပြန်ဖို့သုံး")
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        api_key = key_input.strip() or env_key
        if api_key:
            st.success("✅ Gemini key ရှိတယ်")
        else:
            st.warning("⚠️ Gemini key မရှိသေးဘူး (အဆင့် ၃ အတွက်လိုတယ်)")
        groq_input = st.text_input("Groq API Key", type="password",
                                   placeholder="gsk_...",
                                   help="အသံမှ စာသားထုတ်ဖို့သုံး — console.groq.com မှာ အလကားယူလို့ရ")
        env_groq = os.environ.get("GROQ_API_KEY", "").strip()
        groq_key = groq_input.strip() or env_groq
        if groq_key:
            st.success("✅ Groq key ရှိတယ်")
        else:
            st.warning("⚠️ Groq key မရှိသေးဘူး (အဆင့် ၂ အတွက်လိုတယ်)")
        model_id = st.text_input("Gemini model", value=GEMINI_MODEL_DEFAULT)
        max_speed = st.slider("အမြန်ဆုံးနှုန်း (အသံချုံ့တာ)", 1.0, 2.0, 1.3, 0.05,
                              help="စာရှည်ရင် ဒီနှုန်းအထိ မြန်ပေးမယ်")
        auto_merge = st.checkbox("🔗 အပိုင်းသေးတွေ အလိုအလျောက်ပေါင်း", value=True,
                                 help="Whisper ပေးတဲ့ စက္ကန့်ပိုင်းအကွက်သေးလေးတွေကို "
                                      "ကပ်နေတဲ့အပိုင်းနဲ့ ပေါင်းမယ် — အသံအရမ်းမြန်ရတာသက်သာမယ်။ "
                                      "ပိတ်ထားရင် အရင်အတိုင်း")
        auto_shorten = st.checkbox("✂️ စာရှည်ရင် Gemini နဲ့ အလိုအလျောက်တိုပေး", value=True,
                                   help="အချိန်ကွက်ထဲ မဝင်တဲ့လိုင်းတွေကို Gemini က တိုတိုပြန်ရေးပြီး "
                                        "အသံပြန်ထုတ်မယ် (တစ်ကြိမ်သာ)။ ပိတ်ထားရင် အရင်အတိုင်း")
        voice = st.selectbox("အသံ", [VOICE_MALE, VOICE_FEMALE],
                             format_func=lambda v: "🗣️ ကျား (Thiha)" if v == VOICE_MALE else "🗣️ မ (Nilar)")
        st.divider()
        if st.button("🗑️ အစက ပြန်စ"):
            for k in list(S.keys()):
                del S[k]
            st.rerun()

    # ---------------------------------------------------------- main
    st.header("🎙️ Audio Dub Studio")
    st.caption("ဗီဒီယိုထဲက စကားပြောအပိုင်းတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးတယ် — "
               "မူရင်းဗီဒီယိုအတိုင်း၊ မူရင်းအချိန်အတိုင်း။")

    # ---- အဆင့် ၁: upload
    st.subheader("၁။ ဗီဒီယိုတင်ပါ")
    up = st.file_uploader("MP4 / MOV / WEBM ဖိုင်ရွေးပါ", type=["mp4", "mov", "webm"])
    if S.video_path:
        st.info(f"📁 {os.path.basename(S.video_path)} — {S.duration:.1f} စက္ကန့်")
    if up is not None and st.button("▶️ အသံထုတ်ယူရန်"):
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
                 fitted=None, fit_report=None, out_mp4=None)
        st.success(f"✅ အသံထုတ်ပြီးပြီ — ဗီဒီယို {d:.1f} စက္ကန့်")
        st.rerun()

    # ---- အဆင့် ၂: transcribe
    st.subheader("၂။ အသံမှ စာသားထုတ်")
    if not S.audio_path:
        st.caption("အရင်ဆုံး အဆင့် ၁ မှာ ဗီဒီယိုတင်ပါ။")
    elif not groq_key:
        st.warning("⚠️ Groq API Key ထည့်မှ စာသားထုတ်လို့ရမယ် (ဘယ်ဘက် sidebar)။")
    else:
        if st.button("🎤 နားထောင်ပြီး စာသားထုတ်ရန်"):
            with st.status("Groq Whisper API နဲ့ နားထောင်နေတယ်...", expanded=True) as stt:
                try:
                    data = transcribe_audio(S.audio_path, groq_key)
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

    # ---- အဆင့် ၃: translate
    st.subheader("၃။ မြန်မာလို ဘာသာပြန်")
    if not S.src_segments:
        st.caption("အရင်ဆုံး အဆင့် ၂ မှာ စာသားထုတ်ပါ။")
    elif not api_key:
        st.warning("⚠️ Gemini API key ထည့်မှ ဘာသာပြန်လို့ရမယ် (ဘယ်ဘက် sidebar)။")
    else:
        if st.button("🌐 သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ပြန်ရန်"):
            prog = st.progress(0.0, "Gemini နဲ့ ဘာသာပြန်နေတယ်...")
            try:
                result, failed = gemini_translate(
                    api_key, S.src_segments, model_id.strip() or GEMINI_MODEL_DEFAULT,
                    progress_cb=lambda f: prog.progress(f))
            except Exception as e:
                st.error(f"ဘာသာပြန်တာ ပျက်သွားတယ်: {e}")
                st.stop()
            S.translations, S.final_segments, S.fitted = result, None, None
            prog.empty()
            if failed:
                st.warning(f"⚠️ {len(failed)} ပိုင်း ပြန်မရလို့ မူရင်းစာသားအတိုင်း ထားထားတယ်")
            st.success(f"✅ {len(result)} ပိုင်း ဘာသာပြန်ပြီးပြီ")
        if S.translations:
            with st.expander("ဘာသာပြန်ချက် ကြည့်"):
                for s in S.translations[:30]:
                    st.write(f"`{fmt_ts(s['start'])}` {s['text']}")
                    st.caption(f"မူရင်း: {s['src'][:80]}")

    # ---- အဆင့် ၄: review / edit
    st.subheader("၄။ စာသားစစ် / ပြင်")
    if not S.translations:
        st.caption("အရင်ဆုံး အဆင့် ၃ မှာ ဘာသာပြန်ပါ။")
    else:
        raw = st.text_area(
            "တစ်ကြောင်းချင်း ပြင်လို့ရတယ် — အစဉ်မပြောင်းနဲ့၊ ပုံစံမဖျက်နဲ့",
            value=segments_to_review_text(S.translations), height=300)
        if st.button("✔️ စစ်ပြီး ဆက်ရန်"):
            try:
                S.final_segments = parse_review_text(raw)
                S.fitted, S.out_mp4 = None, None
                st.success(f"✅ {len(S.final_segments)} ပိုင်း အတည်ပြုပြီးပြီ")
            except ValueError as e:
                st.error(str(e))

    # ---- အဆင့် ၅: TTS + fit
    st.subheader("၅။ မြန်မာအသံထုတ် + အချိန်ချိန်")
    if not S.final_segments:
        st.caption("အရင်ဆုံး အဆင့် ၄ မှာ စာသားအတည်ပြုပါ။")
    else:
        st.caption("အသံတစ်ကြောင်းချင်းကို သူ့အချိန်ကွက်ထဲ အတိအကျထည့်မယ် — "
                   "ရှည်ရင် 1.3x အထိ မြန်ပေးမယ်၊ နောက်အပိုင်းနဲ့ ဘယ်တော့မှ မထပ်စေဘူး။")
        if st.button("🔊 အသံထုတ်ရန်"):
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
                                           items)
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
            S.fitted, S.fit_report, S.out_mp4 = fitted, report, None
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

    # ---- အဆင့် ၆: assemble + download
    st.subheader("၆။ ဗီဒီယိုနဲ့ပေါင်း + Download")
    if not S.fitted:
        st.caption("အရင်ဆုံး အဆင့် ၅ မှာ အသံထုတ်ပါ။")
    else:
        if st.button("🎬 မူရင်းဗီဒီယိုနဲ့ ပေါင်းရန်"):
            work_asm = os.path.join(WORK_DIR, S.run_id, "asm")
            dubbed = os.path.join(WORK_DIR, S.run_id, "dubbed_audio.mp3")
            out = os.path.join(WORK_DIR, S.run_id, "dubbed_video.mp4")
            with st.status("အသံဆက် + ဗီဒီယိုနဲ့ပေါင်းနေတယ်...", expanded=False):
                assemble_dubbed(S.fitted, S.duration, work_asm, dubbed)
                mux_video(S.video_path, dubbed, out)
            S.out_mp4 = out
            st.success("✅ ပြီးပြီ! အောက်မှာ download ချလို့ရပြီ")
        if S.out_mp4 and os.path.isfile(S.out_mp4):
            with open(S.out_mp4, "rb") as f:
                st.download_button("⬇️ Dubbed MP4 ရယူ", f,
                                   file_name="dubbed_video.mp4", mime="video/mp4")
        if S.final_segments:
            st.download_button("⬇️ SRT ရယူ",
                               segments_to_srt(S.final_segments),
                               file_name="dubbed.srt", mime="text/plain")


if __name__ == "__main__":
    main()

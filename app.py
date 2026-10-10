#!/usr/bin/env python3
"""Spidy Dub Studio — ဗီဒီယိုထဲက စာသားပြောအပိုင်းတွေကို မြန်မာအသံနဲ့ အစားထိုးပေးတဲ့ tool.

RecapKit ရဲ့ Audio Dub feature ကို တစ်ယောက်စာသုံးဖို့ ပြန်ဆောက်ထားတာ။
Login မလို၊ ငွေမလို — ကိုယ့် Streamlit Cloud မှာ run တယ်။
API key တွေကို browser localStorage မှာ မှတ်ထားတယ် — တစ်ခါထည့်ရုံနဲ့
hard refresh ဆွဲလည်း မပျောက်ဘူး (server Secrets ရှိရင် အဲ့ဒါက အဓိက)။

Pipeline:
  1. MP4 တင် → ffmpeg နဲ့ audio ထုတ် (mp3 16k mono, 32k — Groq 25MB ကန့်သတ်ချက်နဲ့ကိုက်အောင်)
  2. Groq Whisper API (whisper-large-v3) နဲ့ စာသားထုတ် (timestamp ပါ)
     ※ အရင်က local faster-whisper သုံးတာ — Streamlit Cloud ရဲ့ RAM (~1GB)
       ကန့်သတ်ချက်နဲ့ မကိုက်လို့ Groq API နဲ့ လဲထားတာ
     ※ Groq က 403 IP-block ထိရင် AssemblyAI နဲ့ အလိုအလျောက် fallback
       (sidebar toggle + ကိုယ့် AssemblyAI key)
  2b. (optional) အပိုင်းသေးလေးတွေ အလိုအလျောက်ပေါင်း — Whisper ရဲ့ 0.2s လို
      အကွက်သေးတွေကြောင့် အသံအရမ်းမြန်ရတာကို ကာကွယ်ဖို့
  3. Gemini နဲ့ သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ဘာသာပြန်
  4. ပြန်စစ်ပြီး ပြင်လို့ရ (တစ်ကြောင်းချင်း)
  5. edge-tts (my-MM-ThihaNeural) နဲ့ အသံထုတ် → အချိန်ကွက်အတိုင်း ချုံ့/ဖြန့်
  5b. (optional) အချိန်ကွက်ထဲ မဝင်တဲ့လိုင်း → Gemini နဲ့ အလိုအလျောက်တိုအောင်ပြင်
      → အသံပြန်ထုတ် (တစ်ကြိမ်သာ)
  6. ဗီဒီယိုအသစ်နဲ့ ပေါင်း → MP4 download + SRT download

🎬 Recap Studio (sidebar toggle):
  3b. Recap စတိုင်ဘာသာပြန် — စာကြောင်းတိုင်းဘာသာပြန်တာအစား movie recap
      narrator ပြောသလို သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ပြန်ရေး
  6b. Recap render — အသံကို slot ထဲ အတင်းမထည့်ဘဲ သဘာဝအတိုင်းထား,
      video အပိုင်းတစ်ခုချင်းစီကို narration အရှည်နဲ့ကိုက်အောင် setpts နဲ့
      အမြန်/အနှေးချိန် (slow-mo/fast-mo) → dub audio နဲ့ mux

🎙️ Narrator mode (ဗီဒီယိုမုဒ်သာ):
  3'. ffmpeg scene detection → scene တစ်ခုချင်း frame ထုတ် →
     Gemini vision က scene ဖော်ပြချက် → Gemini က third-person မြန်မာ
     narrator script ရေး (scene အလိုက်, အချိန်နဲ့ကိုက်အောင်) →
     S.translations ထဲ ထည့် → အဆင့် ၄/၅/၆ အဟောင်းအတိုင်း ဆက်

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


def _spidey_steps(S, is_video, narr=False):
    """Wizard nav — horizontal stepper (number + status icon), နှိပ်ပြီး ကူးလို့ရ."""
    import streamlit as st
    # ဖုန်း narrow screen မှာ Streamlit က columns တွေကို vertical ပြိုချပစ်တယ် —
    # ၆ ကောလံ stepper ကို တစ်တန်းတည်း ဘေးတိုက်ထိန်းဖို့ CSS
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
/* wizard bottom nav: ခလုတ် ၂ ခု ဘေးချင်းကပ် (marker က ပထမကော်လံထဲ) */
.wiz-bnav-col { display: none; }
/* marker ရဲ့ ကိုယ်ပိုင်အခွံ (stElementContainer) ကိုပဲ layout ကနေ ဖယ် —
   element container တွေက nest မဖြစ်လို့ ဒီ rule က nav row ကို လုံးဝ မထိဘူး */
div[data-testid="stElementContainer"]:has(.wiz-bnav-col) { display: none; }
div[data-testid="stHorizontalBlock"]:has(.wiz-bnav-col) {
    flex-wrap: nowrap !important;
    gap: 0.5rem !important;
}
div[data-testid="stHorizontalBlock"]:has(.wiz-bnav-col) > div {
    min-width: 0 !important;

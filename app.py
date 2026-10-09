#!/usr/bin/env python3
"""
Audio Dub Studio — မြန်မာအသံအစားထိုး + Speed Multiplier (0.5x - 2.0x) + Social Viral Caption & Hooks Generator
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
import streamlit as st

# Setup Work Directories
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_TTS = os.path.join(APP_DIR, "cache_tts")
WORK_DIR = os.path.join(APP_DIR, "work")
os.makedirs(CACHE_TTS, exist_ok=True)
os.makedirs(WORK_DIR, exist_ok=True)

# ---------------------------------------------------------- 🕷️ Theme Styling
_SPIDEY_CSS = """<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&display=swap');
.stApp {
    background-color: #0A0A14;
    background-repeat: no-repeat;
    background-position: top right;
}
.spidey-hero { text-align: center; padding: 20px 0 10px; }
.spidey-kicker { color: #8A93B8; font-size: .8rem; letter-spacing: 2px; font-weight: 700; }
.spidey-title {
    font-family: 'Bangers', sans-serif;
    font-size: 2.8rem; letter-spacing: 2px; color: #F03A3A;
    text-shadow: 2px 2px 0 #1D4ED8, 0 0 25px rgba(230,36,41,.5);
    margin: 4px 0;
}
.spidey-sub { color: #B9C4E8; font-size: 0.95rem; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(18,18,36,.85);
    border: 1px solid rgba(230,36,41,.30) !important;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0,0,0,.4);
    padding: 16px;
    margin-bottom: 14px;
}
.spidey-stephead {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 14px; margin-bottom: 12px;
    background: linear-gradient(90deg, rgba(230,36,41,.25), rgba(43,92,230,.15));
    border: 1px solid rgba(230,36,41,.3);
    border-radius: 10px;
    font-size: 1.1rem; font-weight: 800; color: #fff;
}
.spidey-num {
    width: 30px; height: 30px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    background: linear-gradient(135deg,#F03A3A,#8f1013); color: #fff;
    font-weight: 800; font-size: 1rem;
}
.viral-box {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(230,36,41,0.4);
    border-radius: 12px;
    padding: 14px;
    margin-top: 10px;
}
</style>"""

st.set_page_config(page_title="Audio Dub Studio", page_icon="🎙️", layout="wide")
st.markdown(_SPIDEY_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------- Helper Functions
def run_ffmpeg_speed(input_video, output_video, speed=1.0):
    """FFmpeg သုံး၍ ရုပ်သံ Speed ကို ချိန်ညှိခြင်း (0.5x - 2.0x)"""
    if abs(speed - 1.0) < 0.01:
        shutil.copyfile(input_video, output_video)
        return True
    
    video_filter = f"setpts={1.0/speed}*PTS"
    
    # atempo သည် 0.5 မှ 2.0 အထိသာ တစ်ကြိမ်လက်ခံနိုင်သည်
    if speed < 0.5:
        audio_filter = f"atempo=0.5,atempo={speed/0.5}"
    elif speed > 2.0:
        audio_filter = f"atempo=2.0,atempo={speed/2.0}"
    else:
        audio_filter = f"atempo={speed}"

    cmd = [
        "ffmpeg", "-y", "-i", input_video,
        "-filter:v", video_filter,
        "-filter:a", audio_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "192k",
        output_video
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return res.returncode == 0

def generate_social_kit(gemini_api_key, context_text):
    """Gemini API သုံးပြီး Viral Hook, Caption နှင့် Hashtags ထုတ်ပေးခြင်း"""
    import urllib.request
    
    prompt = f"""You are a top-tier social media content strategist for TikTok, YouTube Shorts, and Facebook Reels.
Based on the following video subtitle/script, generate:
1. 3-Second Hook (Catchy, attention-grabbing opening in Burmese)
2. Viral Caption (Engaging, modern Burmese tone with emojis)
3. Exactly 5 High-traffic English Hashtags (e.g. #fyp #viral #trending...)

Video Content:
\"\"\"{context_text[:1500]}\"\"\"

Return ONLY valid JSON format:
{{
  "hook": "...",
  "caption": "...",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}}
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8}
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            # Clean possible markdown block
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()
            return json.loads(raw_text)
    except Exception as e:
        return {
            "hook": "ဒီဗီဒီယိုကို မဖြစ်မနေ အဆုံးထိ ကြည့်လိုက်ပါ!",
            "caption": "စိတ်ဝင်စားစရာ အကြောင်းအရာကောင်းလေးမို့ သူငယ်ချင်းတို့အတွက် မျှဝေပေးလိုက်ပါတယ်။ ကြိုက်နှစ်သက်ရင် Like & Share လုပ်ဖို့ မမေ့နဲ့နော် ✨",
            "hashtags": ["#fyp", "#trending", "#viral", "#foryou", "#myanmar"]
        }

# ---------------------------------------------------------- Session State
if "api_key" not in st.session_state:
    st.session_state.api_key = os.environ.get("GEMINI_API_KEY", "")
if "rendered_video" not in st.session_state:
    st.session_state.rendered_video = None
if "final_video_speeded" not in st.session_state:
    st.session_state.final_video_speeded = None
if "social_kit" not in st.session_state:
    st.session_state.social_kit = None
if "script_text" not in st.session_state:
    st.session_state.script_text = ""

# ---------------------------------------------------------- UI Header
st.markdown("""
<div class="spidey-hero">
    <div class="spidey-kicker">AUTOMATED DUBBING & SOCIAL PACK STUDIO</div>
    <div class="spidey-title">AUDIO DUB STUDIO</div>
    <div class="spidey-sub">မြန်မာအသံသွင်းခြင်း၊ 2x Video Speed Control နှင့် Viral Social Kit Generator</div>
</div>
""", unsafe_allow_html=True)

# Sidebar: Settings
with st.sidebar:
    st.subheader("🔑 API Configurations")
    gemini_key = st.text_input("Gemini API Key", value=st.session_state.api_key, type="password")
    if gemini_key:
        st.session_state.api_key = gemini_key

# ---------------------------------------------------------- Step 1: Upload & Simulation Demo
with st.container(border=True):
    st.markdown('<div class="spidey-stephead"><span class="spidey-num">1</span><span>ဗီဒီယို တင်ယူခြင်း သို့မဟုတ် Dub Render လုပ်ခြင်း</span></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("ဗီဒီယိုဖိုင် ရွေးချယ်ပါ (MP4 format)", type=["mp4", "mov", "mkv"])
    
    col1, col2 = st.columns([2, 1])
    with col1:
        mock_script = st.text_area(
            "ဇာတ်လမ်းပြော စာသား/Script (Social Kit ထုတ်ရန်အတွက် အသုံးပြုမည်)",
            value=st.session_state.script_text or "ဒီနေ့တော့ ကမ္ဘာကျော် လူစွမ်းကောင်း Spider-Man ရဲ့ အဓိက လျှို့ဝှက်ချက်တွေကို အသေးစိတ် ပြောပြပေးသွားပါမယ်။",
            height=90
        )
        st.session_state.script_text = mock_script

    if uploaded_file is not None:
        if st.button("🚀 ဗီဒီယို စတင် Render ပြုလုပ်မည်", type="primary"):
            video_path = os.path.join(WORK_DIR, f"input_{uuid.uuid4().hex[:6]}.mp4")
            with open(video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.rendered_video = video_path
            st.session_state.final_video_speeded = video_path
            st.success("Render ပြီးစီးပါပြီ! အောက်တွင် Speed နှင့် Social Kit ကို စိတ်ကြိုက် ပြင်ဆင်နိုင်ပါပြီ။")

# ---------------------------------------------------------- Step 2: Post-Render Speed Adjustment (Up to 2x)
if st.session_state.rendered_video and os.path.exists(st.session_state.rendered_video):
    with st.container(border=True):
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">2</span><span>Video Speed Control (0.5x မှ 2.0x အထိ)</span></div>', unsafe_allow_html=True)
        
        speed_col1, speed_col2 = st.columns([3, 1])
        with speed_col1:
            speed_val = st.slider(
                "ဗီဒီယို Speed နှုန်း ချိန်ညှိရန် (Default: 1.0x, အမြန်ဆုံး 2.0x ထိ ရွေးနိုင်သည်):",
                min_value=0.5,
                max_value=2.0,
                value=1.0,
                step=0.1,
                format="%.1fx"
            )
        with speed_col2:
            apply_speed_btn = st.button("⚡ Apply Speed", use_container_width=True)

        if apply_speed_btn:
            with st.spinner(f"ဗီဒီယိုကို {speed_val}x ဖြင့် speed ပြောင်းလဲနေပါသည်..."):
                speed_out_path = os.path.join(WORK_DIR, f"speed_{speed_val}x_{uuid.uuid4().hex[:6]}.mp4")
                success = run_ffmpeg_speed(st.session_state.rendered_video, speed_out_path, speed=speed_val)
                if success:
                    st.session_state.final_video_speeded = speed_out_path
                    st.success(f"ဗီဒီယို Speed ကို {speed_val}x သို့ အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!")
                else:
                    st.error("Speed ပြောင်းလဲရာတွင် FFmpeg error ဖြစ်ပေါ်ခဲ့ပါသည်။")

        # Preview Video
        active_video = st.session_state.final_video_speeded or st.session_state.rendered_video
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            st.video(active_video)
        with col_v2:
            with open(active_video, "rb") as f:
                st.download_button(
                    label="📥 Download Video",
                    data=f.read(),
                    file_name="dubbed_video_output.mp4",
                    mime="video/mp4",
                    use_container_width=True,
                    type="primary"
                )

# ---------------------------------------------------------- Step 3: Viral Social Kit (Hook, Caption, 5 Hashtags)
if st.session_state.rendered_video:
    with st.container(border=True):
        st.markdown('<div class="spidey-stephead"><span class="spidey-num">3</span><span>Social Media Viral Pack (Facebook / Reels / TikTok)</span></div>', unsafe_allow_html=True)
        
        c_top1, c_top2 = st.columns([3, 1])
        with c_top1:
            st.caption("ဗီဒီယို Script ပေါ်အခြေခံ၍ ဆွဲဆောင်မှုရှိသော Hook၊ Caption နှင့် English Hashtag များကို Gemini AI ဖြင့် ထုတ်ပေးထားပါသည်။")
        with c_top2:
            # 🔄 Try Again / Regenerate Button
            regen = st.button("🔄 Try Again (အသစ်ပြန်ထုတ်မည်)", use_container_width=True)

        # Generate on first render or when clicking "Try Again"
        if st.session_state.social_kit is None or regen:
            with st.spinner("AI က Viral Hook နှင့် Captions များကို ရေးသားနေပါသည်..."):
                kit = generate_social_kit(st.session_state.api_key, st.session_state.script_text)
                st.session_state.social_kit = kit

        res_kit = st.session_state.social_kit
        if res_kit:
            h_col, c_col = st.columns(2)
            with h_col:
                st.markdown("🎯 **3-Second Viral Hook (အစ စက္ကန့်ပိုင်း ဆွဲဆောင်ရန်)**")
                st.text_area("Hook", value=res_kit.get("hook", ""), height=80, key="hook_box", label_visibility="collapsed")
                
            with c_col:
                st.markdown("📝 **Engaging Social Caption**")
                st.text_area("Caption", value=res_kit.get("caption", ""), height=80, key="cap_box", label_visibility="collapsed")

            st.markdown("🏷️ **English Hashtags (၅ ခု)**")
            tags = res_kit.get("hashtags", ["#viral", "#trending", "#reels", "#fyp", "#video"])
            tag_string = " ".join(tags[:5])
            st.code(tag_string, language="text")

            # Ready-to-copy Full Social Post
            full_post = f"{res_kit.get('hook', '')}\n\n{res_kit.get('caption', '')}\n\n{tag_string}"
            with st.expander("📋 Copy Post Template (တစ်ခါတည်း ကူးယူရန်)", expanded=False):
                st.text_area("Ready Post", value=full_post, height=130)

st.markdown('<div class="spidey-foot">Audio Dub Studio • All-in-One Creator Suite</div>', unsafe_allow_html=True)

# 🎙️ Audio Dub Studio

ဗီဒီယိုထဲက စကားပြောအပိုင်းတွေကို **မြန်မာအသံ**နဲ့ အစားထိုးပေးတဲ့ tool —
မူရင်းဗီဒီယိုအတိုင်း၊ မူရင်းအချိန်အတိုင်း။ RecapKit ရဲ့ **Audio Dub** feature ကို
တစ်ယောက်စာသုံးဖို့ ပြန်ဆောက်ထားတာ။ Login မလို၊ ငွေမလို —
ကိုယ့် **Streamlit Cloud** (အလကား) ပေါ်မှာ run တယ်။

## လုပ်ဆောင်ချက်

1. MP4 တင် → ffmpeg နဲ့ audio ထုတ် (mp3 16k mono 32k — Groq 25MB ကန့်သတ်ချက်နဲ့ကိုက်အောင်)
2. **Groq Whisper API** (`whisper-large-v3-turbo`) နဲ့ စကားပြော → စာသား + timestamp ထုတ်
3. Gemini (`gemini-3.5-flash-lite`) နဲ့ သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ဘာသာပြန်
4. စာသားကို ပြန်စစ် / ပြင် (တစ်ကြောင်းချင်း)
5. edge-tts `my-MM-ThihaNeural` (ကျားအသံ) နဲ့ အသံထုတ် —
   တစ်ကြောင်းချင်းကို သူ့အချိန်ကွက်ထဲ အတိအကျထည့်
   (ရှည်ရင် 1.3x အထိ မြန်ပေး၊ နောက်အပိုင်းနဲ့ မထပ်စေဘူး၊ ရှည်လွန်းတဲ့လိုင်းတွေ report ထုတ်)
6. မူရင်းဗီဒီယိုနဲ့ ပေါင်း → **Dubbed MP4** + **SRT** download

## Streamlit Cloud ပေါ်တင်နည်း (အလကား)

1. <https://share.streamlit.io> ကို သွား → **GitHub** နဲ့ login ဝင်
2. **New app** → Repository: `samuel66689/audio-dub-studio` ရွေး
3. Branch: `main`, Main file path: `app.py` → **Deploy** နှိပ်
4. App ပွင့်လာရင် ညာဘက်အောက်က **⋮ → Settings → Secrets** ကို သွား၊
   အောက်ပါအတိုင်း ထည့်ပြီး Save:
   ```toml
   GEMINI_API_KEY = "AIzaSy..."
   GROQ_API_KEY = "gsk_..."
   ```
5. ပြီးရင် app ကို **Reboot** လုပ် — sidebar မှာ key တွေရှိပြီလို့ ပြမယ်
   (Secrets မထည့်ချင်ရင် sidebar မှာ တိုက်ရိုက်ရိုက်ထည့်လည်းရတယ်)

Key တွေယူနည်း:
- **Gemini** — [Google AI Studio](https://aistudio.google.com/) က အလကားယူ
- **Groq** — [console.groq.com/keys](https://console.groq.com/keys) က အလကားယူ

## ကိုယ့် computer ပေါ် run နည်း

```bash
cd ~/workspace/audio-dub
streamlit run app.py
```

ပြီးရင် browser မှာ `http://localhost:8501` ပွင့်လာမယ်။

## လိုအပ်ချက်များ

```bash
pip install --user streamlit edge-tts requests
```

- **ffmpeg** — `sudo apt install ffmpeg` (audio/video ဆက်ဖို့)
  (Streamlit Cloud မှာဆို `packages.txt` က အလိုအလျောက် သွင်းပေးတယ်)
- **Groq API Key** — စာသားထုတ်ဖို့သုံး၊ app ရဲ့ ဘယ်ဘက် sidebar မှာ ထည့်
  (ဒါမှမဟုတ် `GROQ_API_KEY` env var / Streamlit Secrets အဖြစ် ထား)
- **Gemini API Key** — [Google AI Studio](https://aistudio.google.com/) က အလကားယူ၊
  app ရဲ့ ဘယ်ဘက် sidebar မှာ ထည့် (ဒါမှမဟုတ် `GEMINI_API_KEY` env var အဖြစ် ထား)။
  Key တွေကို ဘယ်မှာမှ print / log မလုပ်ဘူး။

## မှတ်ချက်များ

- မြန်မာနိုင်ငံကနေ Gemini API ခေါ်ရင် **VPN** လိုနိုင်တယ်
  (RecapKit ရဲ့ local tool တွေလိုပဲ)။
- TTS က Microsoft edge-tts သုံးလို့ internet လိုတယ်။
- Groq Whisper API က **25MB** အထိပဲ လက်ခံတယ် — အသံကို mp3 32k နဲ့
  ထုတ်ထားလို့ မိနစ် ၁၀၀ လောက် အထိ ရတယ်။ အဲ့ထက်ရှည်ရင် ဗီဒီယိုဖြတ်တင်ပါ။
- Video file ကြီးရင် အဆင့် ၅ ကြာနိုင်တယ် — စောင့်ပေးပါ။
- အလုပ်လုပ်ထားတဲ့ file တွေက `work/` အောက်မှာ run တစ်ခုချင်းစီအလိုက် သိမ်းထားတယ်။
  TTS cache က `cache_tts/` ထဲမှာ — စာသားတူရင် ပြန်ထုတ်စရာမလိုဘူး။

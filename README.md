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

## 🎬 Recap Studio (အသစ်)

Sidebar ရဲ့ "⚙️ ရွေးချယ်စရာ" အောက်မှာ toggle ၃ ခု ထပ်ထည့်ထားတယ်
(၃ ခုလုံး **default OFF** — ပိတ်ထားရင် အရင်အတိုင်း အလုပ်လုပ်မယ်)။

- **🎬 Recap စတိုင်နဲ့ ဘာသာပြန်** — စာကြောင်းတိုင်းဘာသာပြန်တာအစား
  movie recap narrator ပြောသလို သဘာဝကျတဲ့ ပြောစကားမြန်မာလို ပြန်ရေးတယ်
  (အဆင့် ၃ မှာသုံးတယ်)။
- **🎞️ Recap render** — အသံကို အချိန်ကွက်ထဲ အတင်းမထည့်ဘဲ သဘာဝအတိုင်းထားပြီး၊
  video အပိုင်းတစ်ခုချင်းစီကို သူ့ narration အရှည်နဲ့ကိုက်အောင် `setpts` နဲ့
  အမြန်/အနှေးချိန်တယ် (slow-mo / fast-mo)။ ပြီးမှ dub audio နဲ့ mux လုပ်တယ်။
  ဘယ် video အပိုင်းကို ဘယ်လောက်ချိန်ထားလဲ အဆင့် ၆ မှာ report ပြတယ်
  (ဥပမာ `#3 x0.67` = အပိုင်း ၃ ကို 1.5x မြန်ထားတယ်)။
  → TikTok/YouTube recap video တန်းတင်လို့ရတဲ့ MP4 ရတယ်။
- **🔥 Subtitle burn-in** — မြန်မာစာတန်းထိုးကို video ထဲ တိုက်ရိုက်ထည့်တယ်
  (Noto Sans Myanmar, အဖြူ+အနက်ဘောင်, 1080p စတိုင်)။ SRT သက်သက်လည်း ရတယ်။
  Recap render နဲ့တွဲသုံးရင် timeline အသစ်နဲ့ကိုက်တဲ့ SRT ရမယ်။

သုံးနည်း: toggle တွေဖွင့် → အဆင့် ၁–၄ အတိုင်းလုပ် → အဆင့် ၆ မှာ
"🎞️ Recap render" နှိပ် → Dubbed MP4 download ချ။

## မှတ်ချက်များ

- မြန်မာနိုင်ငံကနေ Gemini API ခေါ်ရင် **VPN** လိုနိုင်တယ်
  (RecapKit ရဲ့ local tool တွေလိုပဲ)။
- TTS က Microsoft edge-tts သုံးလို့ internet လိုတယ်။
- Groq Whisper API က **25MB** အထိပဲ လက်ခံတယ် — အသံကို mp3 32k နဲ့
  ထုတ်ထားလို့ မိနစ် ၁၀၀ လောက် အထိ ရတယ်။ အဲ့ထက်ရှည်ရင် ဗီဒီယိုဖြတ်တင်ပါ။
- Video file ကြီးရင် အဆင့် ၅ ကြာနိုင်တယ် — စောင့်ပေးပါ။
- Sidebar မှာ toggle ၂ ခု ပါတယ် (နှစ်ခုလုံး default ON):
  - **🔗 အပိုင်းသေးတွေ အလိုအလျောက်ပေါင်း** — Whisper ပေးတဲ့ 0.2s လို
    အကွက်သေးလေးတွေကို ကပ်နေတဲ့အပိုင်းနဲ့ ပေါင်းမယ် (အသံအရမ်းမြန်ရတာ သက်သာမယ်)
  - **✂️ စာရှည်ရင် Gemini နဲ့ အလိုအလျောက်တိုပေး** — အချိန်ကွက်ထဲ မဝင်တဲ့လိုင်းတွေကို
    Gemini က တိုတိုပြန်ရေးပြီး အသံပြန်ထုတ်မယ် (တစ်ကြိမ်သာ)
  - မကြိုက်ရင် ခလုတ်ပိတ်လိုက်ရုံနဲ့ အရင်အတိုင်း ပြန်ဖြစ်မယ်
- အလုပ်လုပ်ထားတဲ့ file တွေက `work/` အောက်မှာ run တစ်ခုချင်းစီအလိုက် သိမ်းထားတယ်။
  TTS cache က `cache_tts/` ထဲမှာ — စာသားတူရင် ပြန်ထုတ်စရာမလိုဘူး။

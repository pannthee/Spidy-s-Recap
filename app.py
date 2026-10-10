```react
import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Play, Pause, Download, Mic, Copy, Activity, Loader2,
  Gauge, CheckCircle2, XCircle, PlayCircle, Clock, Sliders,
  UploadCloud, Wand2, Edit3, DownloadCloud, AlertTriangle,
  Type, RefreshCw, Target, Sparkles, Hand, Check, Zap,
  Image as ImageIcon, BookA, Palette, Settings2, Film, Hash,
  ArrowLeft
} from 'lucide-react';

const VOICES = [
  { id: 'Charon', name: 'အောင်အောင်', gender: 'Male' }, { id: 'Fenrir', name: 'ရဲရင့်', gender: 'Male' },
  { id: 'Orus', name: 'မင်းခန့်', gender: 'Male' }, { id: 'Enceladus', name: 'ဇေယျာ', gender: 'Male' },
  { id: 'Iapetus', name: 'ထက်မြတ်', gender: 'Male' }, { id: 'Algenib', name: 'မျိုးမင်း', gender: 'Male' },
  { id: 'Rasalgethi', name: 'စည်သူ', gender: 'Male' }, { id: 'Schedar', name: 'ကောင်းကင်', gender: 'Male' },
  { id: 'Alnilam', name: 'သီဟ', gender: 'Male' }, { id: 'Sadachbia', name: 'ဝေယံ', gender: 'Male' },
  { id: 'Kore', name: 'စုစု', gender: 'Female' }, { id: 'Aoede', name: 'သန္တာ', gender: 'Female' },
  { id: 'Leda', name: 'လှိုင်', gender: 'Female' }, { id: 'Callirrhoe', name: 'အေးအေး', gender: 'Female' },
  { id: 'Autonoe', name: 'မြမြ', gender: 'Female' }, { id: 'Despina', name: 'နန်းဆု', gender: 'Female' },
  { id: 'Erinome', name: 'ရွှေရည်', gender: 'Female' }, { id: 'Laomedeia', name: 'သီရိ', gender: 'Female' },
  { id: 'Achernar', name: 'မေမီ', gender: 'Female' }, { id: 'Gacrux', name: 'နှင်းနှင်း', gender: 'Female' }
];

const VOICE_STYLES = [
  { id: 'none', label: 'None (Default)' },
  { id: 'Energetic Movie Recap', label: 'Energetic Movie Recap' },
  { id: 'News Anchor', label: 'News Anchor' },
  { id: 'Storyteller', label: 'Storyteller' },
  { id: 'Calm & Professional', label: 'Calm & Professional' },
  { id: 'Horror & Suspense', label: 'Horror & Suspense' },
  { id: 'Romantic & Soft', label: 'Romantic & Soft' },
  { id: 'Comedy & Playful', label: 'Comedy & Playful' },
  { id: 'Action & Thriller', label: 'Action & Thriller' },
  { id: 'Documentary Nature', label: 'Documentary Nature' },
  { id: 'Emotional & Sad', label: 'Emotional & Sad' },
  { id: 'Epic Sci-Fi Narrator', label: 'Epic Sci-Fi Narrator' },
  { id: 'Sarcastic & Witty', label: 'Sarcastic & Witty' },
  { id: 'Anime Protagonist', label: 'Anime Protagonist' },
  { id: 'Friendly Vlogger', label: 'Friendly Vlogger' },
  { id: 'Tech Reviewer', label: 'Tech Reviewer' },
  { id: 'Whispering ASMR', label: 'Whispering ASMR' }
];

const SCRIPT_STYLES = [
  { id: 'none', label: 'None (Default)', prompt: 'Standard cinematic movie recap narration.' },
  { id: 'recap', label: '🎥 Movie Recap', prompt: 'Summarize the entire storyline sequentially into an engaging, complete story from start to finish.' },
  { id: 'documentary', label: '🎞️ Cinematic Documentary', prompt: 'Professional documentary style with dramatic tone, deep insights, and cinematic pacing.' },
  { id: 'storytelling', label: '📖 Storytelling', prompt: 'Natural, casual, and relatable storytelling tone, as if narrating a compelling story to a close friend.' },
  { id: 'viral_short', label: '🔥 Viral Short', prompt: 'Fast-paced short-form style. Start with an ultra-strong 3-second hook to maximize retention and keep the energy high.' },
  { id: 'mystery', label: '🕵️ Mystery / Investigation', prompt: 'Build heavy suspense by revealing clues step-by-step, ending with a climactic plot reveal or twist.' },
  { id: 'horror', label: '👻 Horror / Dark Story', prompt: 'Dark, creepy, and chilling atmosphere with gradual tension buildup and ominous storytelling.' },
  { id: 'news', label: '📰 News / Report', prompt: 'Objective, fact-based, authoritative, and structured presentation like a professional news anchor.' },
  { id: 'explainer', label: '🧠 Explainer / Educational', prompt: 'Clear, concise, educational breakdown explaining the what, why, and how behind the events.' },
  { id: 'emotional', label: '❤️ Emotional Story', prompt: 'Focus heavily on character emotions, touching moments, sadness, joy, and deep audience connection.' },
  { id: 'dramatic_epic', label: '⚡ Dramatic / Epic', prompt: 'Powerful, grandiose narration with epic trailer-like pacing, dramatic build-ups, and punchy lines.' },
  { id: 'biography', label: '👤 Biography / Life Story', prompt: 'Chronological timeline of a person\'s journey, struggles, rise, falls, and achievements.' },
  { id: 'facts_list', label: '💡 Facts / Top List', prompt: 'Curated listicle format (e.g. Top Facts or key points), delivering concise, intriguing facts sequentially.' }
];

const SPEEDS = [
  { id: 'slow', label: 'အနှေး', enLabel: 'Slow', rate: 0.85, emoji: '🐌' },
  { id: 'normal', label: 'ပုံမှန်', enLabel: 'Normal', rate: 1.0, emoji: '▶️️' },
  { id: 'fast', label: 'အမြန်', enLabel: 'Fast', rate: 1.25, emoji: '⚡' }
];

const EMOTIONS = [
  { id: 'Neutral', label: 'ပုံမှန်', enLabel: 'Neutral', emoji: '😐' },
  { id: 'Happy', label: 'ပျော်ရွှင်သော', enLabel: 'Happy', emoji: '😊' },
  { id: 'Sad', label: 'ဝမ်းနည်းသော', enLabel: 'Sad', emoji: '😢' },
  { id: 'Angry', label: 'ဒေါသထွက်သော', enLabel: 'Angry', emoji: '😠' },
  { id: 'Calm', label: 'တည်ငြိမ်သော', enLabel: 'Calm', emoji: '😌' },
  { id: 'Energetic', label: 'တက်ကြွသော', enLabel: 'Energetic', emoji: '⚡' },
  { id: 'Whisper', label: 'တိုးတိုးပြော', enLabel: 'Whispering', emoji: '🤫' },
  { id: 'Storytelling', label: 'ပုံပြင်ပြော', enLabel: 'Storytelling', emoji: '📖' },
  { id: 'Professional', label: 'လုပ်ငန်းသုံး', enLabel: 'Professional', emoji: '👔' },
  { id: 'Casual', label: 'ပေါ့ပေါ့ပါးပါး', enLabel: 'Casual', emoji: '☕' },
  { id: 'Fearful', label: 'ကြောက်ရွံ့သော', enLabel: 'Fearful', emoji: '😨' },
  { id: 'Surprised', label: 'အံ့သြသော', enLabel: 'Surprised', emoji: '😲' },
  { id: 'Excited', label: 'စိတ်လှုပ်ရှားသော', enLabel: 'Excited', emoji: '🤩' },
  { id: 'Romantic', label: 'ချစ်စရာကောင်းသော', enLabel: 'Romantic', emoji: '🥰' },
  { id: 'Sarcastic', label: 'ခနဲ့တဲ့တဲ့', enLabel: 'Sarcastic', emoji: '😏' },
  { id: 'Serious', label: 'လေးနက်သော', enLabel: 'Serious', emoji: '🧐' },
  { id: 'Confident', label: 'ယုံကြည်မှုရှိသော', enLabel: 'Confident', emoji: '😎' },
  { id: 'Shy', label: 'ရှက်တတ်သော', enLabel: 'Shy', emoji: '😳' },
  { id: 'Hopeful', label: 'မျှော်လင့်ချက်ရှိသော', enLabel: 'Hopeful', emoji: '🤞' },
  { id: 'Tired', label: 'ပင်ပန်းနေသော', enLabel: 'Tired', emoji: '😫' }
];

const LOGO_POSITIONS = [
  { id: 'top-left', label: 'Top Left' }, { id: 'top-right', label: 'Top Right' },
  { id: 'bottom-left', label: 'Bottom Left' }, { id: 'bottom-right', label: 'Bottom Right' }
];

const SUBTITLE_COLORS = [
  { id: '#FFFFFF', label: 'အဖြူရောင် (White)', stroke: '#000000' },
  { id: '#FDE047', label: 'အဝါရောင် (Yellow)', stroke: '#000000' },
  { id: '#4ADE80', label: 'အစိမ်းရောင် (Green)', stroke: '#000000' },
  { id: '#22D3EE', label: 'အပြာနုရောင် (Cyan)', stroke: '#000000' },
  { id: '#F472B6', label: 'ပန်းရောင် (Pink)', stroke: '#000000' },
  { id: '#000000', label: 'အမည်းရောင် (Black)', stroke: '#FFFFFF' }
];

const SUBTITLE_BG_PRESETS = ['#000000', '#0f172a', '#1e3a8a', '#991b1b', '#ca8a04'];

const COLOR_TONES = [
  { id: 'Normal (Original)', label: 'Normal (Original)', filter: 'none' },
  { id: 'Cinematic', label: 'Cinematic', filter: 'contrast(1.1) saturate(1.2) brightness(0.9) sepia(0.1)' },
  { id: 'Moody', label: 'Moody', filter: 'contrast(1.2) saturate(0.8) brightness(0.8) sepia(0.2)' },
  { id: 'Vintage', label: 'Vintage', filter: 'sepia(0.4) contrast(1.1) brightness(0.9) hue-rotate(-10deg)' },
  { id: 'Vibrant', label: 'Vibrant', filter: 'saturate(1.5) contrast(1.1)' },
  { id: 'Film Noir', label: 'Film Noir', filter: 'grayscale(1) contrast(1.5) brightness(0.8)' },
  { id: 'Cyberpunk', label: 'Cyberpunk', filter: 'saturate(1.5) contrast(1.2) hue-rotate(15deg) brightness(0.9)' },
  { id: 'Sepia', label: 'Sepia', filter: 'sepia(1) contrast(1.1)' },
  { id: 'Cold Blue', label: 'Cold Blue', filter: 'sepia(0.3) hue-rotate(180deg) saturate(1.2) brightness(0.9)' },
  { id: 'Golden Hour', label: 'Golden Hour', filter: 'sepia(0.4) saturate(1.3) brightness(1.1) contrast(1.1)' },
  { id: 'Muted', label: 'Muted', filter: 'saturate(0.5) contrast(0.9)' },
  { id: 'High Contrast', label: 'High Contrast', filter: 'contrast(1.5)' },
  { id: 'Pastel', label: 'Pastel', filter: 'saturate(0.7) brightness(1.2) contrast(0.8)' },
  { id: 'Dark Matte', label: 'Dark Matte', filter: 'brightness(0.7) contrast(1.2) saturate(0.8)' },
  { id: 'Neon Glow', label: 'Neon Glow', filter: 'saturate(2) contrast(1.3) brightness(1.1)' }
];

// --- CORE HELPERS ---
const apiKey = ""; // Insert your Gemini API Key here
const callGeminiAPI = async (endpoint, payload, retries = 3) => {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${endpoint}?key=${apiKey}`;
  const delays = [1000, 2000, 4000];
  for (let i = 0; i < retries; i++) {
    try {
      const res = await fetch(url, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(`API Error ${res.status}: ${err}`);
      }
      return await res.json();
    } catch (err) {
      if (i === retries - 1) throw err;
      await new Promise(r => setTimeout(r, delays[i]));
    }
  }
};

const parseGeminiJSON = (str) => {
  try {
    let cleanStr = str.replace(/```json/gi, '').replace(/```/g, '').trim();
    const start = cleanStr.indexOf('{');
    const end = cleanStr.lastIndexOf('}');
    if (start !== -1 && end !== -1) {
      return JSON.parse(cleanStr.substring(start, end + 1));
    }
    return JSON.parse(cleanStr);
  } catch (e) {
    throw new Error("AI မှ မှားယွင်းသော format ပြန်ပို့ပါသည်။ (JSON Parse Error) " + e.message);
  }
};

const pcmToWavBlob = (base64Pcm, sampleRate = 24000) => {
  const binaryString = window.atob(base64Pcm);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = binaryString.charCodeAt(i);
  const buffer = new ArrayBuffer(44 + bytes.length);
  const view = new DataView(buffer);
  const writeString = (v, offset, string) => {
    for (let i = 0; i < string.length; i++) v.setUint8(offset + i, string.charCodeAt(i));
  };
  writeString(view, 0, 'RIFF'); view.setUint32(4, 36 + bytes.length, true);
  writeString(view, 8, 'WAVE'); writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  writeString(view, 36, 'data'); view.setUint32(40, bytes.length, true);
  new Uint8Array(buffer, 44).set(bytes);
  return new Blob([buffer], { type: 'audio/wav' });
};

const audioBufferToWavBlob = (buffer) => {
  const numChannels = 1;
  const sampleRate = buffer.sampleRate;
  const channelData = buffer.getChannelData(0);
  const wavBuffer = new ArrayBuffer(44 + channelData.length * 2);
  const view = new DataView(wavBuffer);
  const writeString = (v, offset, string) => {
    for (let i = 0; i < string.length; i++) v.setUint8(offset + i, string.charCodeAt(i));
  };
  writeString(view, 0, 'RIFF');
  view.setUint32(4, 36 + channelData.length * 2, true);
  writeString(view, 8, 'WAVE');
  writeString(view, 12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(view, 36, 'data');
  view.setUint32(40, channelData.length * 2, true);
  let offset = 44;
  for (let i = 0; i < channelData.length; i++) {
    let s = Math.max(-1, Math.min(1, channelData[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    offset += 2;
  }
  return new Blob([wavBuffer], { type: 'audio/wav' });
};

const extractAudioFromVideo = async (file, startSec = 0, endSec = Infinity) => {
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
  const arrayBuffer = await file.arrayBuffer();
  let audioBuffer;
  try {
    audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
  } catch (e) {
    throw new Error("Video မှ အသံခွဲထုတ်၍ မရပါ။ Audio Track မပါဝင်ခြင်း (သို့) Format မထောက်ပံ့ခြင်း ဖြစ်နိုင်ပါသည်။");
  }
  const channelData = audioBuffer.getChannelData(0);
  const startSample = Math.max(0, Math.floor(startSec * 16000));
  const endSample = Math.min(Math.floor(endSec * 16000), channelData.length);
  const sampleCount = endSample - startSample;
  if (sampleCount <= 0) throw new Error("Invalid time range for audio extraction");
  const wavBuffer = new ArrayBuffer(44 + sampleCount * 2);
  const view = new DataView(wavBuffer);
  const writeStr = (offset, str) => { for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i)); };
  writeStr(0, 'RIFF'); view.setUint32(4, 36 + sampleCount * 2, true);
  writeStr(8, 'WAVE'); writeStr(12, 'fmt '); view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); view.setUint16(22, 1, true);
  view.setUint32(24, 16000, true); view.setUint32(28, 16000 * 2, true);
  view.setUint16(32, 2, true); view.setUint16(34, 16, true);
  writeStr(36, 'data'); view.setUint32(40, sampleCount * 2, true);
  let offset = 44;
  for (let i = startSample; i < endSample; i++) {
    let s = Math.max(-1, Math.min(1, channelData[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    offset += 2;
  }
  const blob = new Blob([wavBuffer], { type: 'audio/wav' });
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      if (reader.result) resolve(reader.result.split(',')[1]);
      else reject(new Error("Base64 conversion failed"));
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
};

const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return "00:00";
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = Math.floor(seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

const formatSrtTime = (seconds) => {
  const pad = (num, size) => ('000' + num).slice(size * -1);
  const hrs = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 1000);
  return `${pad(hrs, 2)}:${pad(mins, 2)}:${pad(secs, 2)},${pad(ms, 3)}`;
};

const fixPronunciation = (text) => {
  let fixed = text;
  const fixes = { "ဘီး": "ဘိမ်း", "အံ့သြ": "အံ့အော" };
  for (const [wrong, right] of Object.entries(fixes)) {
    fixed = fixed.split(wrong).join(right);
  }
  return fixed;
};

const generateSubtitleChunks = (text, totalDuration, startTime = 0) => {
  if (!text || totalDuration <= 0) return [];
  let rawSegments = text.split('\n').filter(s => s.trim().length > 0);
  let chunks = [];
  const MAX_LEN = 45;
  rawSegments.forEach(segment => {
    let s = segment.trim();
    while (s.length > MAX_LEN) {
      let splitPos = -1;
      let qPos = s.lastIndexOf('؟', MAX_LEN);
      let commaPos = s.lastIndexOf('၊', MAX_LEN);
      let periodPos = s.lastIndexOf('။', MAX_LEN);
      let spacePos = s.lastIndexOf(' ', MAX_LEN);
      if (periodPos > 10) splitPos = periodPos + 1;
      else if (qPos > 10) splitPos = qPos + 1;
      else if (commaPos > 10) splitPos = commaPos + 1;
      else if (spacePos > 10) splitPos = spacePos;
      if (splitPos === -1) splitPos = MAX_LEN;
      chunks.push(s.substring(0, splitPos).trim());
      s = s.substring(splitPos).trim();
    }
    if (s.length > 0) chunks.push(s);
  });
  if (chunks.length === 0) chunks = [text];
  let pairedChunks = [];
  for (let i = 0; i < chunks.length; i += 2) {
    let pair = chunks[i];
    if (chunks[i + 1]) pair += '\n' + chunks[i + 1];
    pairedChunks.push(pair);
  }
  const chunkWeights = pairedChunks.map(chunk => {
    let w = chunk.replace(/\n/g, '').length + 15;
    if (chunk.includes('။')) w += 10;
    if (chunk.includes('၊')) w += 5;
    if (chunk.includes('?')) w += 5;
    return w;
  });
  const totalWeight = chunkWeights.reduce((a, b) => a + b, 0);
  let subData = [];
  let currentTime = startTime;
  pairedChunks.forEach((chunk, index) => {
    const chunkDuration = (chunkWeights[index] / totalWeight) * totalDuration;
    subData.push({ text: chunk, start: currentTime, end: currentTime + chunkDuration });
    currentTime += chunkDuration;
  });
  return subData;
};

const classNames = (...classes) => classes.filter(Boolean).join(' ');

// --- THUMBNAIL MAKER COMPONENT ---
function ThumbnailMakerComponent() {
  const [thumbText, setThumbText] = useState('');
  const [thumbRatio, setThumbRatio] = useState('16:9');
  const [thumbTextColor, setThumbTextColor] = useState('Neon Cyan & Bright Yellow');
  const [thumbStyle, setThumbStyle] = useState('Epic, dramatic, and cinematic with high contrast');
  const [thumbImages, setThumbImages] = useState([]);
  const [thumbLoading, setThumbLoading] = useState(false);
  const [thumbResultBase64, setThumbResultBase64] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');

  const handleImageUpload = (e) => {
    const files = Array.from(e.target.files);
    files.forEach(file => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result.split(',')[1];
        setThumbImages(prev => [...prev, { url: reader.result, base64: base64, mimeType: file.type }]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeImage = (index) => {
    setThumbImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleGenerateThumbnail = async () => {
    if (!thumbText.trim()) return;
    setThumbLoading(true);
    setThumbResultBase64(null);
    setErrorMsg('');
    try {
      const aspectText = thumbRatio === '16:9' ? "Use a wide 16:9 landscape layout." : "Use a tall 9:16 portrait layout.";
      const refImageText = thumbImages.length > 0 ? " I have provided some reference images. Please incorporate their subjects, visual themes, characters, or layouts seamlessly into the final thumbnail." : "";
      const promptText = `Create a highly engaging, cinematic movie recap style YouTube thumbnail. The image MUST prominently feature this exact text: "${thumbText}".  Text Typography Design: Ensure the text uses ${thumbTextColor} coloring and stands out clearly with movie poster aesthetics. Overall Art Style: ${thumbStyle}.  Make the background epic, dramatic, and highly relevant to the text context.${refImageText} ${aspectText}`;
      const parts = [{ text: promptText }];
      thumbImages.forEach(img => {
        parts.push({
          inlineData: {
            mimeType: img.mimeType,
            data: img.base64
          }
        });
      });
      const payload = {
        contents: [{ parts: parts }],
        generationConfig: { responseModalities: ['TEXT', 'IMAGE'] }
      };
      const data = await callGeminiAPI('gemini-2.5-flash-image-preview:generateContent', payload);
      const base64Image = data.candidates?.[0]?.content?.parts?.find(p => p.inlineData)?.inlineData?.data;
      if (base64Image) {
        setThumbResultBase64(`data:image/jpeg;base64,${base64Image}`);
      } else {
        throw new Error("No image data returned from API.");
      }
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message || "Thumbnail ဖန်တီးရာတွင် အမှားအယွင်းရှိပါသည်။");
    } finally {
      setThumbLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in pt-4">
      <div className="text-center mb-8">
        <h2 className="text-2xl md:text-3xl font-black flex items-center justify-center gap-3 text-cyan-400 tracking-wider uppercase pb-1">
          <Film className="w-8 h-8 text-cyan-400" />
          Movie Poster Maker
        </h2>
        <p className="text-blue-200/60 text-sm mt-2 font-medium tracking-wide">ရုပ်ရှင်ဆန်ဆန် Cinematic Thumbnail များ ဖန်တီးပါ</p>
      </div>
      {errorMsg && (
        <div className="bg-red-950/80 border border-red-500 text-red-100 px-4 py-3 rounded-xl flex items-center gap-3 animate-fade-in">
          <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0" />
          <span className="font-bold text-sm">{errorMsg}</span>
        </div>
      )}
      <div className="bg-[#0a1220]/80 backdrop-blur-xl border border-blue-900/40 rounded-2xl p-6 shadow-2xl">
        <div className="space-y-4">
          <label className="text-sm font-bold text-blue-100 flex items-center gap-2 tracking-wide">
            <BookA className="w-4 h-4 text-cyan-500" /> Thumbnail တွင်ပါဝင်မည့် စာသား (Title Text)
          </label>
          <textarea
            value={thumbText}
            onChange={(e) => setThumbText(e.target.value)}
            placeholder="ဥပမာ - ရုပ်ရှင်အမည် သို့မဟုတ် ဆွဲဆောင်မှုရှိသော စာသား..."
            className="w-full h-24 bg-black/60 border border-blue-900/50 rounded-xl p-4 text-blue-50 outline-none focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 resize-none transition-colors"
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            <div className="space-y-2">
              <label className="text-sm font-bold text-blue-100 flex items-center gap-2 tracking-wide">
                <Palette className="w-4 h-4 text-cyan-500" /> စာသား ကာလာ (Text Color)
              </label>
              <select value={thumbTextColor} onChange={(e) => setThumbTextColor(e.target.value)} className="w-full bg-black/60 border border-blue-900/50 rounded-xl px-4 py-3 text-sm text-blue-50 outline-none focus:border-cyan-500 transition-colors cursor-pointer">
                <option value="Neon Cyan & Bright Yellow">Neon Cyan & Bright Yellow</option>
                <option value="Pure White with Heavy Shadow">Pure White with Heavy Shadow</option>
                <option value="Blood Red & White">Blood Red & White</option>
                <option value="Glowing Green & Dark">Glowing Green & Dark</option>
                <option value="Gold & Luxury Black">Gold & Luxury Black</option>
                <option value="Electric Blue & Crisp White (Modern)">Electric Blue & Crisp White (Modern)</option>
                <option value="Vibrant Magenta & Deep Indigo (Trendy)">Vibrant Magenta & Deep Indigo (Trendy)</option>
                <option value="Sunset Orange & Warm Yellow (Energetic)">Sunset Orange & Warm Yellow (Energetic)</option>
                <option value="Metallic Silver & Ice Blue (Sleek)">Metallic Silver & Ice Blue (Sleek)</option>
                <option value="Bold Yellow & Solid Black (High Impact)">Bold Yellow & Solid Black (High Impact)</option>
              </select>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-bold text-blue-100 flex items-center gap-2 tracking-wide">
                <Wand2 className="w-4 h-4 text-cyan-500" /> ဒီဇိုင်း (Design Style)
              </label>
              <select value={thumbStyle} onChange={(e) => setThumbStyle(e.target.value)} className="w-full bg-black/60 border border-blue-900/50 rounded-xl px-4 py-3 text-sm text-blue-50 outline-none focus:border-cyan-500 transition-colors cursor-pointer">
                <option value="Epic, dramatic, and cinematic movie poster style with high contrast lighting">Epic Movie Poster</option>
                <option value="Dark, mysterious, horror movie style with shadows and fog">Horror & Thriller</option>
                <option value="Sci-Fi cinematic style, neon lights, highly futuristic">Sci-Fi & Cyberpunk</option>
                <option value="Action movie style, explosions, dynamic framing">Action & Explosive</option>
                <option value="Documentary style, realistic, gritty, and historical">Documentary & Gritty</option>
                <option value="Fantasy movie aesthetic, magical glowing elements">Fantasy & Magical</option>
                <option value="3D Rendered, highly detailed cinematic lighting">3D Rendered Cinematic</option>
              </select>
            </div>
          </div>
          <div className="space-y-4 pt-4 mt-2">
            <label className="text-sm font-bold text-blue-100 flex items-center gap-2 tracking-wide">
              <ImageIcon className="w-4 h-4 text-cyan-500" /> Thumbnail တွင်ထည့်ချင်သော ပုံများ (Reference Images)
            </label>
            <div className="flex flex-wrap gap-4 items-center">
              {thumbImages.map((img, i) => (
                <div key={i} className="relative w-24 h-24 rounded-xl overflow-hidden border border-cyan-500/50 group shadow-lg">
                  <img src={img.url} alt={`Ref ${i}`} className="w-full h-full object-cover" />
                  <button onClick={() => removeImage(i)} className="absolute inset-0 bg-black/70 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-sm">
                    <XCircle className="w-8 h-8 text-cyan-500 drop-shadow-md hover:scale-110 transition-transform" />
                  </button>
                </div>
              ))}
              <label className="w-24 h-24 rounded-xl border-2 border-dashed border-blue-900/60 flex flex-col items-center justify-center cursor-pointer hover:border-cyan-500 hover:bg-blue-900/40 transition-all text-blue-400/80 hover:text-cyan-400 group">
                <UploadCloud className="w-7 h-7 mb-1.5 group-hover:scale-110 transition-transform" />
                <span className="text-[10px] font-bold uppercase tracking-wider">Add Image</span>
                <input type="file" accept="image/*" multiple onChange={handleImageUpload} className="hidden" />
              </label>
            </div>
            <p className="text-xs text-blue-200/50 bg-black/30 p-2 rounded-lg border border-blue-900/30 inline-block font-medium">
              ပုံတစ်ပုံထက်ပို၍ ထည့်သွင်းနိုင်ပါသည်။ AI မှ အဆိုပါပုံများကို အခြေခံ၍ ဆွဲပေးပါမည်။
            </p>
          </div>
          <label className="text-sm font-bold text-blue-100 flex items-center gap-2 mt-4 tracking-wide">
            <Settings2 className="w-4 h-4 text-cyan-500" /> ပုံအရွယ်အစား (Aspect Ratio)
          </label>
          <div className="flex gap-4">
            <button onClick={() => setThumbRatio('16:9')} className={classNames("flex-1 py-3 rounded-xl border transition-all flex items-center justify-center gap-2 font-bold", thumbRatio === '16:9' ? "bg-blue-900/40 border-cyan-500 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]" : "bg-black/60 border-blue-900/30 text-blue-200/50 hover:bg-blue-900/20 hover:border-blue-900/50")}>
              <ImageIcon className="w-5 h-4" /> 16:9 (YouTube)
            </button>
            <button onClick={() => setThumbRatio('9:16')} className={classNames("flex-1 py-3 rounded-xl border transition-all flex items-center justify-center gap-2 font-bold", thumbRatio === '9:16' ? "bg-blue-900/40 border-cyan-500 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.2)]" : "bg-black/60 border-blue-900/30 text-blue-200/50 hover:bg-blue-900/20 hover:border-blue-900/50")}>
              <ImageIcon className="w-4 h-5" /> 9:16 (Shorts/Reels)
            </button>
          </div>
          <div className="pt-4 flex gap-3">
            <button onClick={handleGenerateThumbnail} disabled={thumbLoading || !thumbText.trim()} className="flex-[2] bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-black tracking-wide py-4 px-6 rounded-xl shadow-[0_0_15px_rgba(6,182,212,0.3)] transition-all flex items-center justify-center gap-2 disabled:opacity-50 border border-cyan-500/30">
              {thumbLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Sparkles className="w-5 h-5" />}
              {thumbLoading ? "ဖန်တီးနေပါသည်..." : "Thumbnail ဖန်တီးမည်"}
            </button>
            {thumbResultBase64 && (
              <button onClick={handleGenerateThumbnail} disabled={thumbLoading} className="flex-1 bg-black/60 hover:bg-blue-900/30 border border-blue-900/50 text-blue-200 font-bold py-4 px-6 rounded-xl transition-all flex items-center justify-center gap-2 disabled:opacity-50">
                <RefreshCw className={classNames("w-5 h-5", thumbLoading && "animate-spin")} /> Retry
              </button>
            )}
          </div>
        </div>
      </div>
      {thumbResultBase64 && (
        <div className="bg-[#0a1220]/80 border border-cyan-500/30 rounded-2xl p-6 shadow-2xl animate-fade-in-up flex flex-col items-center mt-6">
          <h3 className="text-lg font-bold text-blue-100 mb-6 flex items-center gap-2 w-full tracking-wide">
            <CheckCircle2 className="w-5 h-5 text-cyan-500" /> ရလဒ်
          </h3>
          <div className={classNames("relative rounded-xl overflow-hidden shadow-[0_0_30px_rgba(0,0,0,0.8)] border border-blue-900/50", thumbRatio === '16:9' ? "w-full max-w-2xl aspect-video" : "w-full max-w-sm aspect-[9/16]")}>
            <img src={thumbResultBase64} alt="Generated Thumbnail" className="w-full h-full object-cover" />
          </div>
          <button
            onClick={() => {
              const a = document.createElement('a');
              a.href = thumbResultBase64;
              a.download = `Cinematic_Thumbnail_${Date.now()}.jpg`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }}
            className="mt-6 bg-blue-900/50 hover:bg-blue-800/60 border border-blue-800 hover:border-cyan-500 text-white font-bold py-3 px-8 rounded-xl shadow-lg transition-all flex items-center gap-2 tracking-wide"
          >
            <Download className="w-5 h-5 text-cyan-400" /> ပုံကို ဒေါင်းလုဒ်ဆွဲမည်
          </button>
        </div>
      )}
    </div>
  );
}

// --- MAIN APP COMPONENT ---
export default function App() {
  const [activeTab, setActiveTab] = useState('recap');

  // Settings States
  const [videoFile, setVideoFile] = useState(null);
  const [videoUrl, setVideoUrl] = useState(null);
  const [videoDurationSeconds, setVideoDurationSeconds] = useState(0);

  const [scriptStyle, setScriptStyle] = useState('recap');
  const [isDubbingMode, setIsDubbingMode] = useState(false);
  const [dubbingSpeakers, setDubbingSpeakers] = useState([]);
  const [dubbingDialogues, setDubbingDialogues] = useState([]);

  const [voice, setVoice] = useState('Alnilam');
  const [voiceStyle, setVoiceStyle] = useState('none');
  const [emotion, setEmotion] = useState('Storytelling');
  const [speed, setSpeed] = useState(1.0);
  const [selectedSpeedPreset, setSelectedSpeedPreset] = useState('normal');
  const [isPreviewingVoice, setIsPreviewingVoice] = useState(false);

  const [bypassCopyright, setBypassCopyright] = useState(true);
  const [colorTone, setColorTone] = useState('Normal (Original)');

  // UI View States
  const [showRenderSettings, setShowRenderSettings] = useState(false);

  // Advanced Features
  const [hyperSync, setHyperSync] = useState(false);
  const [enableZoomCrop, setEnableZoomCrop] = useState(false);
  const [videoScale, setVideoScale] = useState(1.0);
  const [videoPanY, setVideoPanY] = useState(0);

  // Interactive Subtitles
  const [enableSubs, setEnableSubs] = useState(true);
  const [subColorObj, setSubColorObj] = useState(SUBTITLE_COLORS[1]);
  const [subFont, setSubFont] = useState('sans-serif');
  const [subX, setSubX] = useState(10);
  const [subY, setSubY] = useState(75);
  const [subW, setSubW] = useState(80);
  const [subH, setSubH] = useState(15);
  const [subStroke, setSubStroke] = useState(15);
  const [subBgOpacity, setSubBgOpacity] = useState(60);
  const [subBgColor, setSubBgColor] = useState('#000000');

  // Interactive Rectangle Blur
  const [blurSubtitles, setBlurSubtitles] = useState(true);
  const [blurX, setBlurX] = useState(10);
  const [blurY, setBlurY] = useState(70);
  const [blurW, setBlurW] = useState(80);
  const [blurH, setBlurH] = useState(25);
  const [blurStrength, setBlurStrength] = useState(25);

  // Drag State
  const dragStateRef = useRef({ mode: null, startX: 0, startY: 0 });
  const [, setForceRender] = useState(0);

  // Logo Settings
  const [logoFile, setLogoFile] = useState(null);
  const [logoUrl, setLogoUrl] = useState(null);
  const [logoImgObj, setLogoImgObj] = useState(null);
  const [logoPos, setLogoPos] = useState('top-right');
  const [logoSize, setLogoSize] = useState(15);
  const [logoOpacity, setLogoOpacity] = useState(100);

  // Export Settings
  const [exportExt, setExportExt] = useState('webm');
  const [aspectRatio, setAspectRatio] = useState('16:9');
  const isRenderingRef = useRef(false);
  const renderStartTimeRef = useRef(null);

  // Core Processing States
  const audioCacheRef = useRef(null);
  const [isGeneratingScript, setIsGeneratingScript] = useState(false);
  const [isGeneratingSocialKit, setIsGeneratingSocialKit] = useState(false);
  const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);

  const [loadingStep, setLoadingStep] = useState('');
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState(null);
  const progressIntervalRef = useRef(null);
  const [previewingSpeakerIdx, setPreviewingSpeakerIdx] = useState(-1);

  const [generatedScript, setGeneratedScript] = useState('');
  const [socialKit, setSocialKit] = useState({ hook3s: '', viralCaption: '', hashtags: [] });
  const [copiedIndex, setCopiedIndex] = useState('');

  const [generatedAudioUrl, setGeneratedAudioUrl] = useState(null);
  const [audioDuration, setAudioDuration] = useState(0);
  const [subtitlesArray, setSubtitlesArray] = useState([]);

  // Render Engine States
  const [isPreviewPlaying, setIsPreviewPlaying] = useState(false);
  const [previewCurrentTime, setPreviewCurrentTime] = useState(0);
  const [isRendering, setIsRendering] = useState(false);
  const [renderProgress, setRenderProgress] = useState(0);
  const [finalVideoUrl, setFinalVideoUrl] = useState(null);

  // Refs
  const videoRef = useRef(null);
  const audioRef = useRef(null);
  const canvasRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const animationFrameRef = useRef(null);
  const recordedChunks = useRef([]);

  // Caching Logo Image
  useEffect(() => {
    if (logoUrl) {
      const img = new Image();
      img.onload = () => setLogoImgObj(img);
      img.src = logoUrl;
    } else {
      setLogoImgObj(null);
    }
  }, [logoUrl]);

  // Adjust Video Speed if HyperSync is ON
  useEffect(() => {
    if (videoRef.current) {
      if (hyperSync && audioDuration > 0 && videoDurationSeconds > 0) {
        const stretchRatio = videoDurationSeconds / audioDuration;
        videoRef.current.playbackRate = stretchRatio;
      } else {
        videoRef.current.playbackRate = 1.0;
      }
    }
  }, [hyperSync, audioDuration, videoDurationSeconds, isPreviewPlaying, isRendering]);

  const startSimulatedProgress = (target = 90) => {
    setProgress(0);
    let p = 0;
    if(progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    progressIntervalRef.current = setInterval(() => {
      p += (target - p) * 0.05;
      if (p >= target - 1) {
        p = target;
        clearInterval(progressIntervalRef.current);
      }
      setProgress(Math.floor(p));
    }, 500);
  };

  const stopSimulatedProgress = () => {
    if(progressIntervalRef.current) clearInterval(progressIntervalRef.current);
    setProgress(100);
  };

  const calculateDimensions = (videoWidth, videoHeight, targetRatio) => {
    if (!videoWidth || !videoHeight) return { w: 1080, h: 1920, x: 0, y: 0, drawW: 1080, drawH: 1920 };
    let canvasW, canvasH;
    if (targetRatio === '16:9') {
      canvasW = 1920; canvasH = 1080;
    } else if (targetRatio === '9:16') {
      canvasW = 1080; canvasH = 1920;
    } else {
      canvasW = 1080; canvasH = 1080;
    }
    const scale = Math.max(canvasW / videoWidth, canvasH / videoHeight);
    const drawW = videoWidth * scale;
    const drawH = videoHeight * scale;
    const x = (canvasW - drawW) / 2;
    const y = (canvasH - drawH) / 2;
    return { w: canvasW, h: canvasH, x, y, drawW, drawH };
  };

  const drawFrame = useCallback(() => {
    if (!canvasRef.current || !videoRef.current || activeTab !== 'recap') return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const video = videoRef.current;
    const dims = calculateDimensions(video.videoWidth, video.videoHeight, aspectRatio);

    if (canvas.width !== dims.w || canvas.height !== dims.h) {
      canvas.width = dims.w;
      canvas.height = dims.h;
    }

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const isExporting = isRenderingRef.current || isRendering || Boolean(finalVideoUrl);

    if (videoUrl && video.videoWidth > 0) {
      if (isPreviewPlaying || isRenderingRef.current) {
        if (video.currentTime >= videoDurationSeconds && !isRenderingRef.current) {
          video.currentTime = 0;
        }
      }

      ctx.save();
      ctx.fillStyle = '#000';
      ctx.fillRect(0, 0, w, h);

      let drawX = dims.x;
      let drawY = dims.y;
      let drawW = dims.drawW;
      let drawH = dims.drawH;

      if (enableZoomCrop) {
          const scaledW = drawW * videoScale;
          const scaledH = drawH * videoScale;
          drawX = drawX - (scaledW - drawW) / 2;
          drawY = drawY - (scaledH - drawH) / 2;

          const panOffset = (videoPanY / 100) * (scaledH / 2);
          drawY += panOffset;

          drawW = scaledW;
          drawH = scaledH;
      }

      if (bypassCopyright) {
        ctx.translate(w, 0);
        ctx.scale(-1, 1);
        ctx.translate(-drawX * 2 - (drawW - w), 0);
      }

      const toneObj = COLOR_TONES.find(t => t.id === colorTone) || COLOR_TONES[0];
      let baseFilter = toneObj.filter;
      if (bypassCopyright) {
        baseFilter = baseFilter === 'none' ? 'contrast(1.05) saturate(1.1)' : `${baseFilter} contrast(1.05) saturate(1.1)`;
      }
      ctx.filter = baseFilter;

      try { ctx.drawImage(video, drawX, drawY, drawW, drawH); } catch(e){}
      ctx.restore();

      if (blurSubtitles) {
        const bx = (blurX / 100) * w;
        const by = (blurY / 100) * h;
        const bw = (blurW / 100) * w;
        const bh = (blurH / 100) * h;
        ctx.save();
        ctx.filter = `blur(${blurStrength}px)`;
        try { ctx.drawImage(canvas, bx, by, bw, bh, bx, by, bw, bh); } catch(e){}
        ctx.restore();

        if (!isExporting && showRenderSettings) {
          const dMode = dragStateRef.current.mode;
          const isBlurActive = dMode && dMode.startsWith('blur');
          ctx.strokeStyle = isBlurActive ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.5)';
          ctx.setLineDash([15, 10]);
          ctx.lineWidth = 4;
          ctx.strokeRect(bx, by, bw, bh);
          ctx.fillStyle = isBlurActive ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.9)';
          ctx.beginPath();
          ctx.arc(bx + bw, by + bh, 15, 0, 2 * Math.PI);
          ctx.fill();
          ctx.fillStyle = isBlurActive ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.7)';
          ctx.font = 'bold 24px sans-serif';
          ctx.textAlign = 'left';
          ctx.textBaseline = 'top';
          ctx.fillText('Blur Area', bx + 10, by + 10);
          ctx.setLineDash([]);
        }
      }
    }

    if (logoImgObj) {
      const logoW = w * (logoSize / 100);
      const logoH = (logoImgObj.height / logoImgObj.width) * logoW;
      const padding = w * 0.03;
      let lx = padding, ly = padding;
      if (logoPos.includes('right')) lx = w - logoW - padding;
      if (logoPos.includes('bottom')) ly = h - logoH - padding;
      ctx.save();
      ctx.globalAlpha = logoOpacity / 100;
      try { ctx.drawImage(logoImgObj, lx, ly, logoW, logoH); } catch(e){}
      ctx.restore();
    }

    if (enableSubs) {
      const sx = (subX / 100) * w;
      const sy = (subY / 100) * h;
      const sw = (subW / 100) * w;
      const sh = (subH / 100) * h;

      if (!isExporting && showRenderSettings) {
        const dMode = dragStateRef.current.mode;
        const isSubActive = dMode && dMode.startsWith('sub');
        ctx.strokeStyle = isSubActive ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.5)';
        ctx.setLineDash([15, 10]);
        ctx.lineWidth = 4;
        ctx.strokeRect(sx, sy, sw, sh);
        ctx.fillStyle = isSubActive ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.9)';
        ctx.beginPath();
        ctx.arc(sx + sw, sy + sh, 15, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = isSubActive ? 'rgba(6, 182, 212, 0.9)' : 'rgba(6, 182, 212, 0.7)';
        ctx.font = 'bold 24px sans-serif';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText('Subtitle Box', sx + 10, sy + 10);
        ctx.setLineDash([]);
      }

      let textToDraw = null;
      if (subtitlesArray.length > 0) {
        let currentTime = 0;
        if (isRenderingRef.current && renderStartTimeRef.current) {
          currentTime = (Date.now() - renderStartTimeRef.current) / 1000;
        } else if (audioRef.current && generatedAudioUrl) {
          currentTime = audioRef.current.currentTime;
        } else {
          currentTime = video.currentTime;
          if (hyperSync && audioDuration > 0 && videoDurationSeconds > 0) {
            currentTime = video.currentTime * (audioDuration / videoDurationSeconds);
          }
          if (currentTime < 0) currentTime = 0;
        }
        const activeSub = subtitlesArray.find(s => currentTime >= s.start && currentTime <= s.end);
        if (activeSub) textToDraw = activeSub.text;
      }

      if (!textToDraw && !isExporting && generatedScript) {
        textToDraw = "Movie Subtitle\n(Placeholder)";
      }

      if (textToDraw) {
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        const fontSize = Math.floor(sh * 0.45);
        ctx.font = `900 ${fontSize}px "${subFont}", sans-serif`;
        const lines = textToDraw.split('\n');
        const totalHeight = lines.length * (fontSize * 1.3);
        const startY = sy + (sh / 2) - (totalHeight / 2) + (fontSize * 0.65);

        lines.forEach((line, i) => {
          const y = startY + (i * (fontSize * 1.3));
          
          if (subBgOpacity > 0) {
            const textWidth = ctx.measureText(line).width;
            const padX = fontSize * 0.6;
            const padY = fontSize * 0.25;
            const rectX = sx + sw/2 - textWidth/2 - padX;
            const rectY = y - fontSize/2 - padY;
            const rectW = textWidth + (padX * 2);
            const rectH = fontSize + (padY * 2);
            const radius = fontSize * 0.3;
            
            const r = parseInt(subBgColor.slice(1, 3), 16) || 0;
            const g = parseInt(subBgColor.slice(3, 5), 16) || 0;
            const b = parseInt(subBgColor.slice(5, 7), 16) || 0;
            
            ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${subBgOpacity / 100})`;
            ctx.beginPath();
            if (ctx.roundRect) ctx.roundRect(rectX, rectY, rectW, rectH, radius);
            else ctx.fillRect(rectX, rectY, rectW, rectH);
            ctx.fill();
          }

          ctx.shadowColor = 'rgba(0, 0, 0, 0.9)';
          ctx.shadowBlur = Math.max(10, Math.floor(fontSize * 0.2));
          ctx.shadowOffsetX = 3;
          ctx.shadowOffsetY = 3;
          
          if (subStroke > 0) {
            ctx.lineWidth = Math.max(1, Math.floor(fontSize * (subStroke / 100)));
            ctx.strokeStyle = subColorObj.stroke;
            ctx.lineJoin = "round";
            ctx.miterLimit = 2;
            ctx.strokeText(line, sx + sw/2, y);
          }
          
          ctx.shadowBlur = 0;
          ctx.shadowOffsetX = 0;
          ctx.shadowOffsetY = 0;
          ctx.fillStyle = subColorObj.id;
          ctx.fillText(line, sx + sw/2, y);
        });
      }
    }

    if (isRenderingRef.current) {
      animationFrameRef.current = setTimeout(drawFrame, 33);
    } else {
      animationFrameRef.current = requestAnimationFrame(drawFrame);
    }
  }, [
    bypassCopyright, blurSubtitles, blurX, blurY, blurW, blurH, blurStrength,
    logoImgObj, logoPos, logoSize, logoOpacity, subColorObj, subFont, subX, subY, subW, subH,
    subStroke, subBgOpacity, subBgColor, enableSubs, subtitlesArray, videoUrl, isRendering, finalVideoUrl,
    generatedAudioUrl, generatedScript, activeTab, videoDurationSeconds, isPreviewPlaying, hyperSync, audioDuration, aspectRatio, colorTone,
    enableZoomCrop, videoScale, videoPanY, showRenderSettings
  ]);

  useEffect(() => {
    if (videoUrl && canvasRef.current && activeTab === 'recap') {
      if (isRenderingRef.current) clearTimeout(animationFrameRef.current);
      else cancelAnimationFrame(animationFrameRef.current);
      drawFrame();
    }
    return () => {
      clearTimeout(animationFrameRef.current);
      cancelAnimationFrame(animationFrameRef.current);
    }
  }, [drawFrame, videoUrl, activeTab]);

  const handleVideoUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (videoUrl) URL.revokeObjectURL(videoUrl);
    if (generatedAudioUrl) URL.revokeObjectURL(generatedAudioUrl);
    if (finalVideoUrl) URL.revokeObjectURL(finalVideoUrl);
    
    setVideoFile(file);
    const newUrl = URL.createObjectURL(file);
    setVideoUrl(newUrl);
    resetFullResults();
    audioCacheRef.current = null;
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (logoUrl) URL.revokeObjectURL(logoUrl);
    setLogoFile(file);
    setLogoUrl(URL.createObjectURL(file));
  };

  const handleFontUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    try {
      const fontName = file.name.replace(/\.[^/.]+$/, "");
      const fontBuffer = await file.arrayBuffer();
      const customFontFace = new FontFace(fontName, fontBuffer);
      await customFontFace.load();
      document.fonts.add(customFontFace);

      setSubFont(fontName);
    } catch (err) {
      console.error("Font upload error:", err);
      setErrorMsg("Font ဖိုင် ထည့်သွင်းရာတွင် အမှားအယွင်းရှိပါသည်။");
    }
  };

  const resetFullResults = () => {
    setGeneratedScript('');
    setSocialKit({ hook3s: '', viralCaption: '', hashtags: [] });
    setDubbingSpeakers([]);
    setDubbingDialogues([]);
    resetAudioResults();
    if(progressIntervalRef.current) clearInterval(progressIntervalRef.current);
  };

  const resetAudioResults = () => {
    if (generatedAudioUrl) URL.revokeObjectURL(generatedAudioUrl);
    if (finalVideoUrl) URL.revokeObjectURL(finalVideoUrl);
    setGeneratedAudioUrl(null);
    setSubtitlesArray([]);
    setFinalVideoUrl(null);
    setProgress(0);
    setErrorMsg(null);
    setIsPreviewPlaying(false);
    setPreviewCurrentTime(0);
    setShowRenderSettings(false);
    if (audioRef.current) audioRef.current.pause();
  };

  const copyToClipboard = (text, id) => {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      if (document.execCommand('copy')) {
        setCopiedIndex(id);
        setTimeout(() => setCopiedIndex(''), 2000);
      }
    } catch (err) {}
    document.body.removeChild(textArea);
  };

  const downloadSRT = () => {
    if (!subtitlesArray || subtitlesArray.length === 0) return;
    let srtContent = '';
    subtitlesArray.forEach((sub, index) => {
      srtContent += `${index + 1}\n`;
      srtContent += `${formatSrtTime(sub.start)} --> ${formatSrtTime(sub.end)}\n`;
      srtContent += `${sub.text}\n\n`;
    });
    const blob = new Blob([srtContent], { type: 'text/srt;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Recap_Subtitles_${Date.now()}.srt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getPointerPos = (e) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const scale = Math.min(rect.width / canvas.width, rect.height / canvas.height);
    const xOffset = (rect.width - canvas.width * scale) / 2;
    const yOffset = (rect.height - canvas.height * scale) / 2;
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    const x = (clientX - rect.left - xOffset) / scale;
    const y = (clientY - rect.top - yOffset) / scale;
    return { px: Math.max(0, Math.min(100, (x / canvas.width) * 100)), py: Math.max(0, Math.min(100, (y / canvas.height) * 100)) };
  };

  const handlePointerDown = (e) => {
    if (isRenderingRef.current || isRendering || finalVideoUrl || !showRenderSettings) return;
    const pos = getPointerPos(e);
    if (!pos) return;
    if (enableSubs) {
      const srX = subX + subW; const srY = subY + subH;
      if (Math.sqrt(Math.pow(pos.px - srX, 2) + Math.pow(pos.py - srY, 2)) < 8) {
        dragStateRef.current = { mode: 'sub-resize', startX: 0, startY: 0 }; setForceRender(prev=>prev+1); return;
      }
      if (pos.px >= subX && pos.px <= srX && pos.py >= subY && pos.py <= srY) {
        dragStateRef.current = { mode: 'sub-move', startX: pos.px - subX, startY: pos.py - subY }; setForceRender(prev=>prev+1); return;
      }
    }
    if (blurSubtitles) {
      const brX = blurX + blurW; const brY = blurY + blurH;
      if (Math.sqrt(Math.pow(pos.px - brX, 2) + Math.pow(pos.py - brY, 2)) < 8) {
        dragStateRef.current = { mode: 'blur-resize', startX: 0, startY: 0 }; setForceRender(prev=>prev+1); return;
      }
      if (pos.px >= blurX && pos.px <= brX && pos.py >= blurY && pos.py <= brY) {
        dragStateRef.current = { mode: 'blur-move', startX: pos.px - blurX, startY: pos.py - blurY }; setForceRender(prev=>prev+1); return;
      }
    }
  };

  const handlePointerMove = (e) => {
    const dState = dragStateRef.current;
    if (!dState.mode) return;
    const pos = getPointerPos(e);
    if (!pos) return;
    if (dState.mode === 'sub-resize') {
      setSubW(Math.max(20, Math.min(100 - subX, pos.px - subX)));
      setSubH(Math.max(5, Math.min(100 - subY, pos.py - subY)));
    } else if (dState.mode === 'sub-move') {
      setSubX(Math.max(0, Math.min(100 - subW, pos.px - dState.startX)));
      setSubY(Math.max(0, Math.min(100 - subH, pos.py - dState.startY)));
    } else if (dState.mode === 'blur-resize') {
      setBlurW(Math.max(10, Math.min(100 - blurX, pos.px - blurX)));
      setBlurH(Math.max(5, Math.min(100 - blurY, pos.py - blurY)));
    } else if (dState.mode === 'blur-move') {
      setBlurX(Math.max(0, Math.min(100 - blurW, pos.px - dState.startX)));
      setBlurY(Math.max(0, Math.min(100 - blurH, pos.py - dState.startY)));
    }
  };

  const handlePointerUp = () => {
    dragStateRef.current = { mode: null, startX: 0, startY: 0 };
    setForceRender(prev=>prev+1);
  };

  const getAudioBase64 = async () => {
    if (audioCacheRef.current) return audioCacheRef.current;
    const base64 = await extractAudioFromVideo(videoFile, 0, videoDurationSeconds);
    audioCacheRef.current = base64;
    return base64;
  };

  const generateScriptFn = async (base64Audio, dubbing = false) => {
    const chunkDurationMinutes = videoDurationSeconds / 60;
    const approxWordCount = Math.max(150, Math.floor(chunkDurationMinutes * 140));
    
    let aiPrompt = "";
    if (dubbing) {
      aiPrompt = `Listen to the audio of this video carefully. This is for a VOICE DUBBING project. Analyze the speakers in the audio. Detect how many distinct speakers there are, and their genders (Male/Female). Translate the EXACT spoken dialogues from the audio into natural Burmese. 

CRITICAL INSTRUCTIONS: 
1. DO NOT summarize the story. 
2. Only translate what the characters are actively saying sequentially. 
3. LINE LENGTH (Canvas Safe Zone): Every single line MUST be short (maximum 35 to 45 Burmese characters). Split sentences at natural pause points.
4. FORMAT: Respond ONLY with a valid JSON object containing two keys:
   - 'speakers': an array of objects like {"id": "Speaker 1", "gender": "Male"}
   - 'dialogues': an array of objects representing each spoken line with precise video timestamps. Format exactly like this:
     [
       {"speaker": "Speaker 1", "start": 2.5, "end": 5.0, "text": "မြန်မာဘာသာပြန် စာသား"},
       {"speaker": "Speaker 2", "start": 5.2, "end": 8.1, "text": "နောက်ထပ် မြန်မာဘာသာပြန်"}
     ]`;
    } else {
      const activeStyle = SCRIPT_STYLES.find(s => s.id === scriptStyle) || SCRIPT_STYLES[1];
      aiPrompt = `Listen to the audio of this video. Act as a professional narrator. Translate and summarize the storyline into natural Burmese.

WRITING STYLE & TONE GUIDELINE: ${activeStyle.prompt}

CRITICAL SCRIPT PACING & BREATHING RULES:
1. STRONG HOOK (First 5 Seconds):
   - The very first sentence MUST be an ultra-compelling, high-retention hook that immediately grabs the viewer's attention within the first 5 seconds.

2. SENTENCE CADENCE & NATURAL MIX:
   - Mix short, punchy statements (3-6 words) with medium-length sentences (7-10 words).
   - NEVER write long, run-on sentences. Ensure the flow mimics authentic, conversational human storytelling.

3. STRATEGIC PUNCTUATION FOR AUDIO BREATHING:
   - Place commas (၊) at natural pauses to allow the TTS voice to take a short micro-breath.
   - Use full stops (။) decisively at the end of thoughts for clean vocal cadence and natural deceleration.

4. DOUBLE LINE BREAKS (\\n\\n) FOR TOPIC TRANSITIONS:
   - Whenever transitioning between distinct scenes, key plot points, or dramatic shifts, insert a double line break (\\n\\n).
   - This creates a crucial silence gap in the narration so the AI voice does not sound rushed or robotic.

5. CANVAS & CLEAN TEXT COMPATIBILITY:
   - Keep individual subtitle cues between 35 to 45 Burmese characters per line.
   - Do NOT output timestamps, Markdown asterisks (*), bracketed tags [], or extraneous numbering in the script text.
   - Format: Return ONLY a valid JSON object with the key 'script'.`;
    }

    const payload = {
      contents: [{ parts: [{ text: aiPrompt }, { inlineData: { mimeType: "audio/wav", data: base64Audio } }] }],
      generationConfig: { responseMimeType: "application/json" }
    };

    const data = await callGeminiAPI('gemini-2.5-flash:generateContent', payload);
    return parseGeminiJSON(data.candidates[0].content.parts[0].text);
  };

  const generateSocialKitFn = async (base64Audio) => {
    const aiPrompt = `Listen to the audio from this video. Generate a structured JSON for a MOVIE RECAP video social media post.
    Return EXACTLY this JSON structure:
    {
      "hook3s": "A high-retention 3-second hook (in Burmese) designed to stop viewers scrolling.",
      "viralCaption": "A punchy, cinematic viral social media caption (in Burmese).",
      "hashtags": ["#MovieRecap", "#CinemaRecap", "#Trending", "#FilmReview", "#MustWatch"] // Array of exactly 5 trending English hashtags
    }`;
    const payload = {
      contents: [{ parts: [{ text: aiPrompt }, { inlineData: { mimeType: "audio/wav", data: base64Audio } }] }],
      generationConfig: { responseMimeType: "application/json" }
    };
    const data = await callGeminiAPI('gemini-2.5-flash:generateContent', payload);
    return parseGeminiJSON(data.candidates[0].content.parts[0].text);
  };

  const handleInitialGenerate = async () => {
    if (!videoFile) { setErrorMsg("ကျေးဇူးပြု၍ Video ဖိုင် ရွေးချယ်ပါ။"); return; }
    setIsGeneratingScript(true);
    setIsGeneratingSocialKit(true);
    resetFullResults();
    setErrorMsg(null);
    startSimulatedProgress(85);
    try {
      setLoadingStep('Video မှ အသံကို ခွဲထုတ်နေပါသည်...');
      const base64Audio = await getAudioBase64();
      setLoadingStep(isDubbingMode ? 'AI မှ Dubbing Script နှင့် Voice Character များ ခွဲခြားနေပါသည်...' : 'AI မှ ရုပ်ရှင် Recap Script ဖန်တီးနေပါသည်...');
      const [scriptResultObj, socialKitResult] = await Promise.all([
        generateScriptFn(base64Audio, isDubbingMode),
        generateSocialKitFn(base64Audio)
      ]);
      
      if (isDubbingMode && scriptResultObj.speakers) {
        const dialogues = scriptResultObj.dialogues || [];
        setDubbingDialogues(dialogues);
        setGeneratedScript(dialogues.map(d => `[${d.speaker}]: ${d.text}`).join('\n'));
        
        setDubbingSpeakers(scriptResultObj.speakers.map(s => {
          const defVoice = VOICES.find(v => v.gender === s.gender) || VOICES.find(v => v.gender === 'Male');
          return { ...s, mappedVoice: defVoice ? defVoice.id : 'Charon' };
        }));
      } else {
        setGeneratedScript(scriptResultObj.script || scriptResultObj || '');
      }
      
      setSocialKit(socialKitResult || { hook3s: '', viralCaption: '', hashtags: [] });
      stopSimulatedProgress();
      setLoadingStep('အောင်မြင်ပါသည်!');
    } catch (err) {
      console.error(err);
      if(progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      setErrorMsg(err.message || "အမှားအယွင်းဖြစ်ပွားခဲ့ပါသည်။ Format မှားယွင်းခြင်း (သို့) Video အရမ်းရှည်လွန်းနေခြင်း ဖြစ်နိုင်ပါသည်။");
    } finally {
      setTimeout(() => { setIsGeneratingScript(false); setIsGeneratingSocialKit(false); }, 500);
    }
  };

  const handleRetryScript = async () => {
    setIsGeneratingScript(true);
    setErrorMsg(null);
    startSimulatedProgress(90);
    try {
      setLoadingStep(isDubbingMode ? 'AI မှ Dubbing Script အသစ် ပြန်ရေးနေပါသည်...' : 'AI မှ Recap Script အသစ် ပြန်ရေးနေပါသည်...');
      const base64Audio = await getAudioBase64();
      const scriptResultObj = await generateScriptFn(base64Audio, isDubbingMode);
      
      if (isDubbingMode && scriptResultObj.speakers) {
        const dialogues = scriptResultObj.dialogues || [];
        setDubbingDialogues(dialogues);
        setGeneratedScript(dialogues.map(d => `[${d.speaker}]: ${d.text}`).join('\n'));

        setDubbingSpeakers(scriptResultObj.speakers.map(s => {
          const defVoice = VOICES.find(v => v.gender === s.gender) || VOICES.find(v => v.gender === 'Male');
          return { ...s, mappedVoice: defVoice ? defVoice.id : 'Charon' };
        }));
      } else {
        setGeneratedScript(scriptResultObj.script || scriptResultObj || '');
      }
      
      stopSimulatedProgress();
    } catch (err) {
      console.error(err);
      if(progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      setErrorMsg("Script အသစ်ထုတ်ရာတွင် အမှားအယွင်းရှိပါသည်။ (API Error)");
    } finally {
      setTimeout(() => setIsGeneratingScript(false), 500);
    }
  };

  const handleRetrySocialKit = async () => {
    setIsGeneratingSocialKit(true);
    setErrorMsg(null);
    try {
      const base64Audio = await getAudioBase64();
      const socialKitResult = await generateSocialKitFn(base64Audio);
      setSocialKit(socialKitResult || { hook3s: '', viralCaption: '', hashtags: [] });
    } catch (err) {
      console.error(err);
      setErrorMsg("Social Kit အသစ်ထုတ်ရာတွင် အမှားအယွင်းရှိပါသည်။");
    } finally {
      setIsGeneratingSocialKit(false);
    }
  };

  const playVoicePreview = async (voiceIdToTest = null, speakerIdx = -1) => {
    if (isPreviewingVoice || previewingSpeakerIdx !== -1) return;
    const actualVoiceToTest = voiceIdToTest || voice;
    
    if (speakerIdx !== -1) {
       setPreviewingSpeakerIdx(speakerIdx);
    } else {
       setIsPreviewingVoice(true);
    }
    
    try {
      const emotionObj = EMOTIONS.find(e=>e.id===emotion) || EMOTIONS[0];
      const fixedScriptForAudio = fixPronunciation("မင်္ဂလာပါ။ ကျွန်တော့်အသံကို အခုလို ကြားရတဲ့အတွက် ဝမ်းသာပါတယ်။");
      
      let styleText = voiceStyle !== 'none' ? `\nStyle / Persona: ${voiceStyle}` : '';
      const ttsPrompt = `Make the voice sound ${emotionObj.enLabel}, at a speed of ${speed}x pace:${styleText}\n\n${fixedScriptForAudio}`;
      
      const payload = {
        contents: [{ parts: [{ text: ttsPrompt }] }],
        generationConfig: {
          responseModalities: ["AUDIO"],
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: actualVoiceToTest } } }
        }
      };
      
      let data;
      try {
        data = await callGeminiAPI('gemini-2.5-flash-preview-tts:generateContent', payload);
      } catch (err) {
        payload.contents[0].parts[0].text = fixedScriptForAudio;
        data = await callGeminiAPI('gemini-2.5-flash-preview-tts:generateContent', payload);
      }
      
      const audioPart = data.candidates?.[0]?.content?.parts?.find(p => p.inlineData);
      if(audioPart?.inlineData?.data) {
        const ttsBase64 = audioPart.inlineData.data;
        const mimeType = audioPart.inlineData.mimeType || "audio/wav";
        
        let finalWavBlob;
        if (mimeType.includes('audio/L16') || mimeType.includes('audio/pcm')) {
          let sampleRate = 24000;
          if (mimeType.includes('rate=')) {
            const match = mimeType.match(/rate=(\d+)/);
            if (match && match[1]) sampleRate = parseInt(match[1], 10);
          }
          finalWavBlob = pcmToWavBlob(ttsBase64, sampleRate);
        } else if (ttsBase64.startsWith('UklGRg') || ttsBase64.startsWith('SUQz') || ttsBase64.startsWith('//') || ttsBase64.startsWith('AAAA')) {
          const res = await fetch(`data:${mimeType};base64,${ttsBase64}`);
          finalWavBlob = await res.blob();
        } else {
          finalWavBlob = pcmToWavBlob(ttsBase64, 24000);
        }
        
        const url = URL.createObjectURL(finalWavBlob);
        const audio = new Audio(url);
        await audio.play();
        audio.onended = () => {
            setIsPreviewingVoice(false);
            setPreviewingSpeakerIdx(-1);
        };
      } else {
        throw new Error("No audio data returned");
      }
    } catch (err) {
      console.error("Test Voice Error:", err);
      setIsPreviewingVoice(false);
      setPreviewingSpeakerIdx(-1);
    }
  };

  const handleGenerateAudioOnly = async () => {
    if (!generatedScript) { setErrorMsg("Script မရှိသေးပါ။ ကျေးဇူးပြု၍ Script အရင်ထုတ်ပါ။"); return; }
    setIsGeneratingAudio(true);
    resetAudioResults();
    startSimulatedProgress(80);
    
    try {
      const lines = generatedScript.split('\n').filter(l => l.trim().length > 0);
      let decodedBuffers = []; 
      let ttsSubs = [];
      let currentTimeline = 0;
      let lineCount = 0;
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        lineCount++;
        setLoadingStep(`အသံထုတ်လုပ်နေပါသည်... (${lineCount}/${lines.length})`);
        
        let textToSpeak = line;
        let currentVoiceId = voice;
        let startSec = currentTimeline;
        
        if (isDubbingMode) {
          const match = line.match(/^\[?(.*?)\]?\s*:\s*(.*)$/);
          if (match) {
            let possibleSpeaker = match[1].trim();
            textToSpeak = match[2].trim();
            const sp = dubbingSpeakers.find(s => s.id === possibleSpeaker || s.id.includes(possibleSpeaker));
            if (sp && sp.mappedVoice) currentVoiceId = sp.mappedVoice;
          }
          if (dubbingDialogues[i] && dubbingDialogues[i].start !== undefined) {
            startSec = parseFloat(dubbingDialogues[i].start);
          }
        }
        
        let cleanText = textToSpeak
          .replace(/\*/g, '')
          .replace(/\[.*?\]/g, '')
          .replace(/\(.*?\)/g, '')
          .replace(/[။၊]{2,}/g, '။')
          .trim();

        if (!cleanText || cleanText.length < 2) continue;
        
        const fixedScriptForAudio = fixPronunciation(cleanText);
        let apiVoice = currentVoiceId;
        if (!VOICES.find(v => v.id === currentVoiceId)) apiVoice = 'Charon';
        
        const emotionObj = EMOTIONS.find(e=>e.id===emotion) || EMOTIONS[0];
        const styleText = voiceStyle !== 'none' ? `\nStyle / Persona: ${voiceStyle}` : '';

        if (i > 0) {
            await new Promise(r => setTimeout(r, 400));
        }

        let success = false;
        let attempts = 0;
        const maxAttempts = 2;

        while (attempts < maxAttempts && !success) {
            attempts++;
            try {
                const ttsPrompt = `Make the voice sound ${emotionObj.enLabel}, at a speed of ${speed}x pace:${styleText}\n\n${fixedScriptForAudio}`;
                
                const payload = {
                  contents: [{ parts: [{ text: ttsPrompt }] }],
                  generationConfig: {
                    responseModalities: ["AUDIO"],
                    speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: apiVoice } } }
                  }
                };
                
                let data;
                try {
                  data = await callGeminiAPI('gemini-2.5-flash-preview-tts:generateContent', payload);
                  if (data?.candidates?.[0]?.finishReason === 'SAFETY') throw new Error("SAFETY");
                  if (!data?.candidates?.[0]?.content?.parts?.find(p => p.inlineData)) throw new Error("NO_AUDIO");
                } catch (err) {
                  console.warn(`Fallback TTS request for line ${lineCount} due to error:`, err);
                  payload.contents[0].parts[0].text = fixedScriptForAudio;
                  data = await callGeminiAPI('gemini-2.5-flash-preview-tts:generateContent', payload);
                }
                
                const candidate = data.candidates?.[0];
                if (candidate?.finishReason === 'SAFETY') {
                   throw new Error(`စာကြောင်း (${lineCount}) တွင် Safety Policy နှင့်ငြိစွန်းသော စာသားပါဝင်နေသဖြင့် အသံထုတ်မရပါ။`);
                }
                
                const audioPart = candidate?.content?.parts?.find(p => p.inlineData);
                if(!audioPart?.inlineData?.data) {
                    throw new Error(`အသံဒေတာ မရရှိပါ။ (Line: ${lineCount})`);
                }
                
                const ttsBase64 = audioPart.inlineData.data;
                const mimeType = audioPart.inlineData.mimeType || "audio/wav";
                
                let finalWavBlob;
                if (mimeType.includes('audio/L16') || mimeType.includes('audio/pcm')) {
                  let sampleRate = 24000;
                  if (mimeType.includes('rate=')) {
                    const match = mimeType.match(/rate=(\d+)/);
                    if (match && match[1]) sampleRate = parseInt(match[1], 10);
                  }
                  finalWavBlob = pcmToWavBlob(ttsBase64, sampleRate);
                } else if (ttsBase64.startsWith('UklGRg') || ttsBase64.startsWith('SUQz') || ttsBase64.startsWith('//')) {
                  const res = await fetch(`data:${mimeType};base64,${ttsBase64}`);
                  finalWavBlob = await res.blob();
                } else {
                  finalWavBlob = pcmToWavBlob(ttsBase64, 24000);
                }
                
                const arrayBuffer = await finalWavBlob.arrayBuffer();
                const decodedData = await audioCtx.decodeAudioData(arrayBuffer);
                
                decodedBuffers.push({ buffer: decodedData, startSec: startSec });
                
                const dur = decodedData.duration;
                ttsSubs.push(...generateSubtitleChunks(cleanText, dur, startSec));
                
                if (isDubbingMode) {
                    currentTimeline = Math.max(currentTimeline, startSec + dur);
                } else {
                    currentTimeline += dur;
                }

                success = true;
            } catch (err) {
                console.warn(`Attempt ${attempts} failed for line ${lineCount}. Error:`, err.message);
                if (attempts < maxAttempts) {
                    await new Promise(r => setTimeout(r, 2000));
                } else {
                    console.warn(`Line ${lineCount} failed to generate audio. Skipping.`);
                }
            }
        }
      }
      
      setLoadingStep('အသံများကို ပေါင်းစပ်နေပါသည်...');
      
      let maxEndSec = isDubbingMode ? (videoDurationSeconds || 0) : 0;
      for (const item of decodedBuffers) {
          if (item.startSec + item.buffer.duration > maxEndSec) {
              maxEndSec = item.startSec + item.buffer.duration;
          }
      }
      
      const totalSamples = Math.ceil(maxEndSec * 24000);
      const finalBuffer = audioCtx.createBuffer(1, totalSamples, 24000);
      const finalChannelData = finalBuffer.getChannelData(0);
      
      for (const item of decodedBuffers) {
          const startSample = Math.floor(item.startSec * 24000);
          const channelData = item.buffer.getChannelData(0);
          for (let j = 0; j < channelData.length; j++) {
              if (startSample + j < totalSamples) {
                  finalChannelData[startSample + j] += channelData[j];
              }
          }
      }
      
      const mergedWavBlob = audioBufferToWavBlob(finalBuffer);
      const newAudioUrl = URL.createObjectURL(mergedWavBlob);
      
      setAudioDuration(finalBuffer.duration);
      setGeneratedAudioUrl(newAudioUrl);
      setSubtitlesArray(ttsSubs);
      
      stopSimulatedProgress();
      setLoadingStep('လုပ်ငန်းစဉ် အောင်မြင်ပါသည်!');
      
    } catch (err) {
      console.error("Audio Gen Error:", err);
      if(progressIntervalRef.current) clearInterval(progressIntervalRef.current);
      setErrorMsg(err.message || "အသံဖန်တီးရာတွင် အမှားအယွင်းရှိပါသည်။ စာသားအရမ်းရှည်ပါက အနည်းငယ်လျှော့ပေးပါ။");
    } finally {
      setTimeout(() => setIsGeneratingAudio(false), 500);
    }
  };

  const togglePreviewPlay = () => {
    if (!videoRef.current) return;
    
    if (isPreviewPlaying) {
      videoRef.current.pause();
      if (audioRef.current) audioRef.current.pause();
      setIsPreviewPlaying(false);
    } else {
      videoRef.current.muted = true;
      let vidTime = 0;
      
      if (audioRef.current && generatedAudioUrl) {
          vidTime = audioRef.current.currentTime;
          if (hyperSync && audioDuration > 0 && videoDurationSeconds > 0) {
             const stretchRatio = videoDurationSeconds / audioDuration;
             vidTime = audioRef.current.currentTime * stretchRatio;
          }
          audioRef.current.play();
      } else {
          vidTime = previewCurrentTime;
      }
      
      videoRef.current.currentTime = vidTime;
      videoRef.current.play();
      setIsPreviewPlaying(true);
    }
  };

  const handleSeek = (e) => {
    const time = parseFloat(e.target.value);
    setPreviewCurrentTime(time);
    
    if (audioRef.current && generatedAudioUrl) {
      audioRef.current.currentTime = time;
    }
    
    if (videoRef.current) {
      let vidTime = time;
      if (generatedAudioUrl && hyperSync && audioDuration > 0 && videoDurationSeconds > 0) {
        const stretchRatio = videoDurationSeconds / audioDuration;
        vidTime = time * stretchRatio;
      }
      videoRef.current.currentTime = vidTime;
    }
  };

  const handleAudioTimeUpdate = () => {
    if (audioRef.current) setPreviewCurrentTime(audioRef.current.currentTime);
  };

  const handleRenderFinalVideo = async () => {
    const audioSource = generatedAudioUrl;
    if (!audioSource || !canvasRef.current || !videoRef.current) return;
    
    isRenderingRef.current = true;
    setIsRendering(true);
    setRenderProgress(0);
    recordedChunks.current = [];
    setIsPreviewPlaying(false);
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const canvasStream = canvas.captureStream(30);
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const dest = audioCtx.createMediaStreamDestination();
    
    try {
      const audioRes = await fetch(audioSource);
      const audioBlob = await audioRes.blob();
      const audioBuffer = await audioCtx.decodeAudioData(await audioBlob.arrayBuffer());
      const bufferSource = audioCtx.createBufferSource();
      bufferSource.buffer = audioBuffer;
      bufferSource.connect(dest);
      
      const combinedStream = new MediaStream([
        ...canvasStream.getVideoTracks(),
        ...dest.stream.getAudioTracks()
      ]);
      
      let selectedMime = '';
      let ext = 'mp4';
      const mp4Types = ['video/mp4;codecs=avc1.42E01E,mp4a.40.2', 'video/mp4;codecs=h264,aac', 'video/mp4'];
      const webmTypes = ['video/webm;codecs=vp9,opus', 'video/webm;codecs=vp8,opus', 'video/webm'];
      
      for (const t of mp4Types) {
        if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(t)) { selectedMime = t; ext = 'mp4'; break; }
      }
      if (!selectedMime) {
        for (const t of webmTypes) {
          if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(t)) { selectedMime = t; ext = 'webm'; break; }
        }
      }
      
      setExportExt(ext);
      const options = selectedMime ? { mimeType: selectedMime } : {};
      const mediaRecorder = new MediaRecorder(combinedStream, options);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) recordedChunks.current.push(e.data);
      };
      
      mediaRecorder.onstop = async () => {
        const mimeForBlob = mediaRecorder.mimeType || (ext === 'mp4' ? 'video/mp4' : 'video/webm');
        let blob = new Blob(recordedChunks.current, { type: mimeForBlob });
        
        if (ext === 'webm' && window.ysFixWebmDuration && audioDuration > 0) {
          try {
            const durationMs = Math.floor(audioDuration * 1000);
            blob = await new Promise(resolve => window.ysFixWebmDuration(blob, durationMs, resolve));
          } catch (e) {
            console.error("WebM Duration Fix Error:", e);
          }
        }
        
        if(finalVideoUrl) URL.revokeObjectURL(finalVideoUrl);
        setFinalVideoUrl(URL.createObjectURL(blob));
        isRenderingRef.current = false;
        setIsRendering(false);
        video.playbackRate = 1.0;
        video.loop = false;
      };
      
      video.currentTime = 0;
      video.muted = true;
      video.loop = true;
      
      if (hyperSync && audioDuration > 0 && videoDurationSeconds > 0) {
        const stretchRatio = videoDurationSeconds / audioDuration;
        video.playbackRate = stretchRatio;
      } else {
        video.playbackRate = 1.0;
      }
      
      await video.play();
      bufferSource.start(0);
      renderStartTimeRef.current = Date.now();
      mediaRecorder.start(1000);
      
      if(audioRef.current) audioRef.current.currentTime = 0;
      
      const duration = audioBuffer.duration;
      let elapsed = 0;
      const interval = setInterval(() => {
        elapsed += 0.5;
        const pct = Math.min((elapsed / duration) * 100, 99);
        setRenderProgress(pct);
      }, 500);
      
      bufferSource.onended = () => {
        clearInterval(interval);
        setRenderProgress(100);
        setTimeout(() => {
          if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') mediaRecorderRef.current.stop();
          video.pause();
          if (audioRef.current) audioRef.current.pause();
        }, 500);
      };
    } catch (e) {
      console.error(e);
      setErrorMsg("Video ထုတ်ယူရာတွင် အမှားအယွင်းရှိပါသည်။ (Render Error)");
      isRenderingRef.current = false;
      setIsRendering(false);
    }
  };

  const downloadFinalVideo = () => {
    if (!finalVideoUrl) return;
    const a = document.createElement('a');
    a.href = finalVideoUrl;
    a.download = `Cinematic_Recap_${Date.now()}.${exportExt}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // Mini Player UI Component reusable
  const renderMiniPlayer = () => (
    <div className="w-full bg-[#0a1220] border border-blue-900/40 rounded-xl p-3 flex flex-col gap-2 shadow-lg z-10 relative">
      <div className="flex items-center gap-4 px-2">
        <button onClick={togglePreviewPlay} className="text-cyan-500 hover:text-cyan-400 transition-colors p-1.5 bg-blue-950/50 rounded-full hover:bg-blue-900/50 border border-blue-900/50 shadow-[0_0_10px_rgba(6,182,212,0.2)]">
          {isPreviewPlaying ? <Pause className="w-5 h-5"/> : <Play className="w-5 h-5 ml-0.5"/>}
        </button>
        <span className="text-xs font-mono font-bold text-cyan-300 w-12 text-right">
          {formatTime(previewCurrentTime)}
        </span>
        <input 
          type="range" 
          min="0" 
          max={(generatedAudioUrl ? audioDuration : videoDurationSeconds) || 1} 
          step="0.1" 
          value={previewCurrentTime} 
          onChange={handleSeek} 
          className="flex-1 accent-cyan-500 h-1.5 bg-blue-950/50 rounded-lg appearance-none cursor-pointer" 
        />
        <span className="text-xs font-mono font-bold text-cyan-300 w-12">
          {formatTime((generatedAudioUrl ? audioDuration : videoDurationSeconds))}
        </span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050b14] text-slate-50 font-sans p-4 md:p-8 relative overflow-hidden font-mm selection:bg-cyan-500/30">
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/20 via-[#050b14] to-[#020617] pointer-events-none z-0"></div>
      <div className="relative z-10 max-w-7xl mx-auto pb-20">
        
        <div className="flex justify-center gap-4 mb-8 mt-4 relative z-10">
          <button onClick={() => setActiveTab('recap')} className={`px-6 py-3 rounded-xl font-bold transition-all border tracking-wide uppercase text-sm ${activeTab === 'recap' ? 'bg-blue-700 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.4)]' : 'bg-[#0a1220] border-blue-900/30 text-blue-200/50 hover:bg-blue-900/30 hover:text-blue-200'}`}>
            <Film className="w-5 h-5 inline-block mr-2 -mt-1"/> Director's Cut
          </button>
          <button onClick={() => setActiveTab('thumbnail')} className={`px-6 py-3 rounded-xl font-bold transition-all border tracking-wide uppercase text-sm ${activeTab === 'thumbnail' ? 'bg-blue-700 border-cyan-500 text-white shadow-[0_0_20px_rgba(6,182,212,0.4)]' : 'bg-[#0a1220] border-blue-900/30 text-blue-200/50 hover:bg-blue-900/30 hover:text-blue-200'}`}>
            <ImageIcon className="w-5 h-5 inline-block mr-2 -mt-1"/> Poster Maker
          </button>
        </div>

        {activeTab === 'thumbnail' ? (
          <ThumbnailMakerComponent />
        ) : (
          <div className="space-y-8">
            <header className="text-center space-y-3 pt-2">
              <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-950/50 border border-cyan-500/30 text-cyan-400 text-sm font-bold mb-2 shadow-[0_0_15px_rgba(6,182,212,0.2)] tracking-widest uppercase">
                <Film className="w-4 h-4"/> Cinematic Experience
              </div>
              <h1 className="text-4xl md:text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-indigo-400 pb-1 flex items-center justify-center gap-3 uppercase">
                Movie Recap Studio
              </h1>
              <p className="text-blue-200/70 text-sm md:text-base max-w-2xl mx-auto leading-relaxed font-medium">
                Video တစ်ခုလုံးကို AI မှ ဆွဲဆောင်မှုအပြည့်ရှိသော ရုပ်ရှင် Recap အဖြစ် Script ဖန်တီးပေးပါမည်။
              </p>
            </header>

            {errorMsg && (
              <div className="bg-red-950/80 border border-red-500 text-red-100 px-6 py-4 rounded-xl flex items-center justify-center gap-3 animate-fade-in shadow-[0_0_20px_rgba(239,68,68,0.3)]">
                <AlertTriangle className="w-6 h-6 text-red-500 flex-shrink-0" />
                <span className="font-bold text-sm tracking-wide">{errorMsg}</span>
                <button onClick={()=>setErrorMsg(null)} className="ml-auto bg-red-900 p-1.5 rounded-lg hover:bg-red-800 transition-colors"><XCircle className="w-5 h-5"/></button>
              </div>
            )}

            {/* MAIN CONDITIONAL LAYOUT WRAPPER */}
            <div className={showRenderSettings ? "grid grid-cols-1 xl:grid-cols-12 gap-8 flex flex-col-reverse xl:flex-row" : "flex flex-col"}>
              
              {/* LEFT PANEL / MAIN COLUMN */}
              <div className={showRenderSettings ? "xl:col-span-5 space-y-6 order-2 xl:order-1" : "max-w-4xl mx-auto w-full space-y-6 animate-fade-in"}>
                
                {!showRenderSettings ? (
                  <>
                    <div className="bg-[#0a1220]/80 backdrop-blur-xl border border-blue-900/40 rounded-2xl p-6 shadow-2xl hover:border-cyan-500/50 transition-colors group">
                      <h3 className="text-lg font-black text-cyan-500 flex items-center gap-2 mb-4 border-b border-blue-900/40 pb-2 tracking-wide uppercase">
                        ၁။ ရုပ်ရှင် Video ရွေးချယ်ပါ
                      </h3>
                      <div>
                        <input type="file" accept="video/*" onChange={handleVideoUpload} className="hidden" id="video-upload" />
                        <label htmlFor="video-upload" className="flex flex-col items-center justify-center w-full p-8 border-2 border-dashed border-blue-900/50 rounded-xl cursor-pointer hover:border-cyan-500 hover:bg-blue-900/20 transition-all text-sm font-medium text-blue-200/50">
                          <UploadCloud className="w-12 h-12 text-blue-900/50 group-hover:text-cyan-500 mb-4 transition-colors" />
                          {videoFile ? (
                            <div className="flex flex-col items-center gap-2">
                              <span className="text-cyan-300 bg-blue-950/80 px-4 py-2 rounded-lg text-xs font-mono break-all line-clamp-1 border border-blue-800/50 shadow-inner tracking-wide">{videoFile.name}</span>
                              {videoDurationSeconds > 0 && <span className="text-xs text-cyan-400 font-bold bg-black/50 px-2 py-1 rounded">Full Video Duration: {formatTime(videoDurationSeconds)}</span>}
                            </div>
                          ) : (
                            <span className="font-bold tracking-wider">Click to Upload Video File</span>
                          )}
                        </label>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="bg-gradient-to-r from-blue-950/50 to-black/50 p-4 rounded-xl border border-blue-900/50 shadow-inner group transition-all hover:border-cyan-500/50">
                        <label className="text-sm font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 flex items-center gap-2 tracking-wide uppercase mb-2">
                          <BookA className="w-4 h-4 text-cyan-500" /> Script Writing Style
                        </label>
                        <select
                          value={scriptStyle}
                          onChange={e=>setScriptStyle(e.target.value)}
                          className="w-full bg-black/60 border border-blue-900/50 rounded-lg px-3 py-2.5 outline-none focus:border-cyan-500 text-sm transition-colors cursor-pointer text-blue-100"
                        >
                          {SCRIPT_STYLES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                        </select>
                        <p className="text-[10px] text-blue-200/60 mt-2 font-bold leading-relaxed">
                          {SCRIPT_STYLES.find(s => s.id === scriptStyle)?.prompt}
                        </p>
                      </div>

                      <div className="flex flex-col gap-2 bg-gradient-to-r from-blue-950/50 to-black/50 p-4 rounded-xl border border-blue-900/50 shadow-inner group transition-all hover:border-cyan-500/50 relative overflow-hidden">
                        <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
                          <Mic className="w-24 h-24 text-cyan-500" />
                        </div>
                        <div className="flex items-center justify-between relative z-10">
                          <div>
                            <span className="text-sm font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 flex items-center gap-2 tracking-wide uppercase">
                              <Mic className="w-4 h-4 text-cyan-500" /> Voice Dubbing Mode
                            </span>
                            <p className="text-[10px] text-blue-200/60 mt-1 font-bold">မူရင်းအသံကို ဘာသာပြန်ပြီး အသံထပ်သွင်းမည် (Dubbing) / ပိတ်ထားပါက Recap အကျဉ်းချုပ်ဖန်တီးမည်</p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
                            <input type="checkbox" checked={isDubbingMode} onChange={e=>setIsDubbingMode(e.target.checked)} className="sr-only peer" />
                            <div className="w-11 h-6 bg-blue-950/80 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-blue-200 after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-blue-600 peer-checked:to-cyan-500 shadow-[0_0_10px_rgba(0,0,0,0.5)]"></div>
                          </label>
                        </div>
                      </div>

                      {!generatedScript && (
                        <button
                          onClick={handleInitialGenerate}
                          disabled={isGeneratingScript || !videoFile}
                          className="w-full bg-blue-900/20 border-2 border-blue-900 hover:border-cyan-500 hover:bg-blue-900/40 text-white font-black tracking-wide text-lg py-5 px-6 rounded-2xl transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:scale-100 flex flex-col items-center justify-center relative overflow-hidden group shadow-[0_0_15px_rgba(6,182,212,0.1)]"
                        >
                          {isGeneratingScript && (
                            <div className="absolute top-0 left-0 bottom-0 bg-cyan-500/20 transition-all duration-300" style={{ width: `${progress}%` }} />
                          )}
                          <div className="relative z-10 flex items-center gap-3">
                            {isGeneratingScript ? <Loader2 className="w-6 h-6 animate-spin text-cyan-500"/> : <Edit3 className="w-6 h-6 text-cyan-500 group-hover:-rotate-12 transition-transform"/>}
                            <span className={isGeneratingScript ? "text-cyan-300" : ""}>{isGeneratingScript ? "ဇာတ်ညွှန်းရေးသားနေပါသည်..." : "Script & Titles ထုတ်မည်"}</span>
                          </div>
                          {isGeneratingScript && <span className="text-xs font-bold mt-2 relative z-10 bg-black/60 px-3 py-1 rounded-md text-cyan-300 border border-blue-900/50">{loadingStep} ({progress}%)</span>}
                        </button>
                      )}
                    </div>

                    {generatedScript && (
                      <div className="bg-[#0a1220]/80 backdrop-blur-xl border border-cyan-500/50 rounded-2xl p-6 shadow-[0_0_30px_rgba(6,182,212,0.15)] animate-fade-in-up space-y-4">
                        <div className="flex items-center justify-between border-b border-blue-900/40 pb-3">
                          <h3 className="font-black text-cyan-400 flex items-center gap-2 text-lg tracking-wide uppercase">
                            <Check className="w-5 h-5" /> ၂။ Director's Script
                          </h3>
                          <button onClick={handleRetryScript} disabled={isGeneratingScript} className="text-xs font-bold bg-black/50 hover:bg-blue-950 text-cyan-300 px-3 py-1.5 rounded-lg border border-blue-900/50 flex items-center gap-2 transition-colors disabled:opacity-50">
                            <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingScript ? 'animate-spin' : ''}`} /> Script အသစ်ရေးမည်
                          </button>
                        </div>
                        <div className="relative group">
                          <textarea
                            value={generatedScript}
                            onChange={(e) => setGeneratedScript(e.target.value)}
                            className="w-full h-64 bg-black text-[14.5px] leading-relaxed text-slate-50 p-5 rounded-xl border border-blue-900/50 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 outline-none resize-none transition-colors shadow-inner"
                            placeholder="AI မှ ရေးသားထားသော စာသားများ ဤနေရာတွင် ပေါ်လာပါမည်..."
                          />
                          <div className="absolute bottom-3 left-3 pointer-events-none opacity-60 transition-opacity">
                            <span className="bg-black/80 border border-blue-900/50 text-cyan-300 text-[10px] font-bold px-2.5 py-1.5 rounded-lg tracking-widest uppercase shadow-sm backdrop-blur-sm">
                              Word Count: {generatedScript.trim().split(/\s+/).filter(Boolean).length}
                            </span>
                          </div>
                          <div className="absolute bottom-3 right-3 pointer-events-none opacity-50 group-focus-within:opacity-100 transition-opacity">
                            <span className="bg-blue-900/80 text-white text-[10px] font-bold px-2 py-1 rounded tracking-widest uppercase">Editable</span>
                          </div>
                        </div>
                        <p className="text-xs text-blue-200/60 bg-black/40 p-3 rounded-lg border border-blue-900/40 leading-relaxed font-medium">
                          <b className="text-cyan-400 font-black">အကြံပြုချက်:</b> စာကြောင်းရှည်များကို စာပိုဒ်ခွဲပေးခြင်းဖြင့် Video တွင် စာတန်းထိုးပေါ်လာသည့်အခါ ဖတ်ရပိုအဆင်ပြေစေပါသည်။
                        </p>
                      </div>
                    )}

                    {generatedScript && (socialKit.hook3s || socialKit.viralCaption) && (
                      <div className="bg-[#0a1220]/80 backdrop-blur-xl border border-blue-900/40 rounded-2xl p-6 shadow-2xl animate-fade-in-up">
                        <div className="flex items-center justify-between mb-6 border-b border-blue-900/40 pb-3">
                          <h3 className="font-black text-blue-100 flex items-center gap-2 text-lg tracking-wide uppercase">
                            <Sparkles className="w-5 h-5 text-cyan-500" /> Social Media Launch Kit
                          </h3>
                          <button onClick={handleRetrySocialKit} disabled={isGeneratingSocialKit} className="text-xs font-bold bg-black/50 hover:bg-blue-950/50 text-cyan-300 px-3 py-1.5 rounded-lg border border-blue-900/50 flex items-center gap-2 transition-colors disabled:opacity-50">
                            <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingSocialKit ? 'animate-spin' : ''}`} /> Regenerate Kit
                          </button>
                        </div>
                        
                        <div className="flex flex-col gap-4">
                          {socialKit.hook3s && (
                            <div className={`bg-black/60 p-5 rounded-2xl border flex flex-col gap-3 shadow-lg group transition-all relative overflow-hidden ${copiedIndex === 'hook' ? 'border-cyan-500 bg-blue-950/30' : 'border-blue-900/40 hover:border-cyan-500/50'}`}>
                              <div className="flex items-start justify-between gap-4">
                                <div>
                                   <div className="text-[10px] font-black mb-1.5 uppercase tracking-widest text-cyan-500 flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" /> 3-Sec Hook (TikTok/Reels)</div>
                                   <p className="text-sm font-bold leading-snug text-slate-50">{socialKit.hook3s}</p>
                                </div>
                                <button onClick={() => copyToClipboard(socialKit.hook3s, 'hook')} className={`shrink-0 p-2.5 rounded-lg transition-colors border ${copiedIndex === 'hook' ? 'bg-cyan-600 border-cyan-500 text-white' : 'bg-blue-950/50 border-blue-900/50 text-cyan-400 hover:bg-blue-900/80 hover:text-white'}`}>
                                  {copiedIndex === 'hook' ? <CheckCircle2 className="w-5 h-5"/> : <Copy className="w-5 h-5"/>}
                                </button>
                              </div>
                            </div>
                          )}
                          
                          {socialKit.viralCaption && (
                            <div className={`bg-black/60 p-5 rounded-2xl border flex flex-col gap-3 shadow-lg group transition-all relative overflow-hidden ${copiedIndex === 'caption' ? 'border-cyan-500 bg-blue-950/30' : 'border-blue-900/40 hover:border-cyan-500/50'}`}>
                              <div className="flex items-start justify-between gap-4">
                                <div>
                                   <div className="text-[10px] font-black mb-1.5 uppercase tracking-widest text-cyan-500 flex items-center gap-1.5"><Type className="w-3.5 h-3.5" /> Viral Caption</div>
                                   <p className="text-sm font-bold leading-snug text-slate-50">{socialKit.viralCaption}</p>
                                </div>
                                <button onClick={() => copyToClipboard(socialKit.viralCaption, 'caption')} className={`shrink-0 p-2.5 rounded-lg transition-colors border ${copiedIndex === 'caption' ? 'bg-cyan-600 border-cyan-500 text-white' : 'bg-blue-950/50 border-blue-900/50 text-cyan-400 hover:bg-blue-900/80 hover:text-white'}`}>
                                  {copiedIndex === 'caption' ? <CheckCircle2 className="w-5 h-5"/> : <Copy className="w-5 h-5"/>}
                                </button>
                              </div>
                            </div>
                          )}

                          {socialKit.hashtags && socialKit.hashtags.length > 0 && (
                            <div className={`bg-black/60 p-4 rounded-xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm transition-all ${copiedIndex === 'hashtags' ? 'border-cyan-500 bg-blue-950/30' : 'border-blue-900/40'}`}>
                               <div className="flex flex-wrap gap-2">
                                 {socialKit.hashtags.map((tag, i) => (
                                    <span key={i} className="text-xs font-bold text-cyan-300 bg-blue-950/50 px-2.5 py-1 rounded-md border border-blue-900/50 flex items-center gap-0.5">
                                      {tag}
                                    </span>
                                 ))}
                               </div>
                               <button onClick={() => copyToClipboard(socialKit.hashtags.join(' '), 'hashtags')} className={`w-full sm:w-auto text-xs font-bold px-4 py-2 rounded-lg transition-colors border whitespace-nowrap flex items-center justify-center gap-2 uppercase tracking-wide ${copiedIndex === 'hashtags' ? 'bg-cyan-600 border-cyan-500 text-white' : 'bg-blue-950/50 border-blue-900/50 text-cyan-400 hover:bg-blue-900/80 hover:text-white'}`}>
                                  {copiedIndex === 'hashtags' ? <CheckCircle2 className="w-4 h-4"/> : <Hash className="w-4 h-4"/>} 
                                  {copiedIndex === 'hashtags' ? 'Copied Tags' : 'Copy Tags'}
                                </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {generatedScript && (
                      <>
                        <div className="bg-[#0a1220]/80 backdrop-blur-xl border border-blue-900/40 rounded-2xl p-6 shadow-2xl hover:border-cyan-500/30 transition-colors">
                          <h3 className="text-lg font-black text-cyan-400 flex items-center gap-2 mb-4 border-b border-blue-900/40 pb-2 tracking-wide uppercase">
                            ၃။ Narrator Voice Setting
                          </h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {isDubbingMode && dubbingSpeakers.length > 0 ? (
                              <div className="col-span-1 md:col-span-2 space-y-3 mb-2">
                                <label className="text-xs font-bold text-blue-200/70 uppercase tracking-wider flex items-center gap-1"><Mic className="w-3.5 h-3.5 text-cyan-500"/> Voice Character Assignments</label>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                  {dubbingSpeakers.map((sp, idx) => (
                                    <div key={idx} className="flex flex-col gap-2 bg-black/40 p-2.5 rounded-xl border border-blue-900/50">
                                      <div className="flex items-center gap-2">
                                        <div className="flex flex-col flex-1">
                                          <span className="text-xs font-bold text-blue-100 line-clamp-1">{sp.id}</span>
                                          <span className="text-[10px] text-cyan-400 font-medium uppercase">{sp.gender}</span>
                                        </div>
                                        <select
                                          value={sp.mappedVoice}
                                          onChange={(e) => {
                                            const newSp = [...dubbingSpeakers];
                                            newSp[idx].mappedVoice = e.target.value;
                                            setDubbingSpeakers(newSp);
                                          }}
                                          className="flex-[1.5] bg-blue-950/40 border border-blue-900/50 rounded-lg px-2 py-1.5 outline-none focus:border-cyan-500 text-xs text-blue-100 cursor-pointer"
                                        >
                                          {VOICES.map(v => <option key={v.id} value={v.id}>{v.name} ({v.gender})</option>)}
                                        </select>
                                      </div>
                                      <button 
                                        onClick={() => playVoicePreview(sp.mappedVoice, idx)} 
                                        disabled={previewingSpeakerIdx !== -1 || isPreviewingVoice} 
                                        className="w-full text-cyan-400 hover:text-white bg-blue-950/30 hover:bg-blue-900/50 px-2 py-1.5 rounded-lg border border-blue-900/50 flex items-center justify-center gap-1.5 transition-colors text-[10px] font-bold uppercase tracking-wider disabled:opacity-50"
                                      >
                                        {previewingSpeakerIdx === idx ? <Loader2 className="w-3 h-3 animate-spin"/> : <Play className="w-3 h-3"/>} Test Voice
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <div>
                                <label className="text-xs font-bold text-blue-200/70 mb-1.5 flex items-center justify-between uppercase tracking-wider">
                                  <span className="flex items-center gap-1"><Mic className="w-3.5 h-3.5 text-cyan-500"/> Voice Actor</span>
                                  <button onClick={() => playVoicePreview(voice)} disabled={isPreviewingVoice} className="text-cyan-400 hover:text-white bg-blue-950/50 px-2 py-0.5 rounded border border-blue-900/50 flex items-center gap-1 transition-colors">
                                     {isPreviewingVoice ? <Loader2 className="w-3 h-3 animate-spin"/> : <Play className="w-3 h-3"/>} <span className="text-[10px]">Test Voice</span>
                                  </button>
                                </label>
                                <select value={voice} onChange={e=>setVoice(e.target.value)} className="w-full bg-black border border-blue-900/50 rounded-lg px-3 py-2.5 outline-none focus:border-cyan-500 text-sm transition-colors cursor-pointer text-blue-100">
                                  {VOICES.map(v => <option key={v.id} value={v.id}>{v.name} ({v.gender})</option>)}
                                </select>
                              </div>
                            )}
                            
                            <div>
                              <label className="text-xs font-bold text-blue-200/70 mb-1.5 flex items-center gap-1 uppercase tracking-wider">
                                <Wand2 className="w-3.5 h-3.5 text-cyan-500"/> Voice Style
                              </label>
                              <select value={voiceStyle} onChange={e=>setVoiceStyle(e.target.value)} className="w-full bg-black border border-blue-900/50 rounded-lg px-3 py-2.5 outline-none focus:border-cyan-500 text-sm transition-colors cursor-pointer text-blue-100">
                                {VOICE_STYLES.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
                              </select>
                            </div>

                            <div>
                              <label className="text-xs font-bold text-blue-200/70 mb-1.5 flex items-center gap-1 uppercase tracking-wider"><Activity className="w-3.5 h-3.5 text-cyan-500"/> Emotion</label>
                              <select value={emotion} onChange={e=>setEmotion(e.target.value)} className="w-full bg-black border border-blue-900/50 rounded-lg px-3 py-2.5 outline-none focus:border-cyan-500 text-sm transition-colors cursor-pointer text-blue-100">
                                {EMOTIONS.map(e => <option key={e.id} value={e.id}>{e.emoji} {e.label} ({e.enLabel})</option>)}
                              </select>
                            </div>

                            <div className={isDubbingMode && dubbingSpeakers.length > 0 ? "col-span-1 md:col-span-2 flex flex-col justify-center gap-1.5 mt-0.5" : "flex flex-col justify-center gap-1.5 mt-0.5"}>
                              <label className="text-xs font-bold text-blue-200/70 flex justify-between uppercase tracking-wider mb-1">
                                <span><Gauge className="w-3.5 h-3.5 inline mr-1 text-cyan-500"/> Speed Presets</span>
                              </label>
                              <div className="flex gap-2">
                                {SPEEDS.map(s => (
                                  <button
                                    key={s.id}
                                    onClick={() => { setSelectedSpeedPreset(s.id); setSpeed(s.rate); }}
                                    className={`flex-1 py-2 px-1 rounded-lg border text-xs font-bold transition-all flex flex-col items-center justify-center gap-1 ${selectedSpeedPreset === s.id ? 'bg-blue-900/60 border-cyan-500 text-cyan-300 shadow-[0_0_10px_rgba(6,182,212,0.3)]' : 'bg-black/60 border-blue-900/50 text-blue-200/60 hover:bg-blue-900/40 hover:text-blue-100'}`}
                                  >
                                    <span className="text-sm">{s.emoji}</span>
                                    <span>{s.label}</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="space-y-4 pt-2">
                          <button
                            onClick={handleGenerateAudioOnly}
                            disabled={isGeneratingAudio}
                            className={`w-full ${generatedAudioUrl ? 'bg-blue-900/40 border-cyan-500 hover:bg-blue-900/60' : 'bg-gradient-to-r from-blue-700 via-blue-600 to-cyan-600 hover:from-blue-600 hover:to-cyan-500 border-cyan-500/50'} text-white font-black tracking-wider text-lg py-5 px-6 rounded-2xl shadow-[0_0_30px_rgba(6,182,212,0.4)] transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 flex items-center justify-center relative overflow-hidden group border`}
                          >
                            {isGeneratingAudio && (
                              <div className="absolute top-0 left-0 bottom-0 bg-white/20 transition-all duration-300" style={{ width: `${progress}%` }} />
                            )}
                            <div className="relative z-10 flex items-center gap-3">
                              {isGeneratingAudio ? <Loader2 className="w-7 h-7 animate-spin"/> : (generatedAudioUrl ? <RefreshCw className="w-6 h-6 group-hover:rotate-180 transition-transform duration-500"/> : <Mic className="w-7 h-7 group-hover:scale-110 transition-transform"/>)}
                              <span className="uppercase">{isGeneratingAudio ? "Processing Audio..." : (generatedAudioUrl ? "အသံ အသစ်ပြန်ပြောင်းမည် (Regenerate Audio)" : "AI အသံ ထုတ်လုပ်မည် (Generate Audio)")}</span>
                            </div>
                            {isGeneratingAudio && <span className="text-xs font-bold mt-2 relative z-10 bg-black/60 px-3 py-1 rounded-md text-blue-200 border border-blue-900/50">{loadingStep} ({progress}%)</span>}
                          </button>
                          
                          {(videoUrl || generatedAudioUrl) && (
                            <div className="space-y-4 pt-4 border-t border-blue-900/40 mt-6 animate-fade-in-up">
                              {renderMiniPlayer()}

                              {generatedAudioUrl && (
                                <button
                                  onClick={() => setShowRenderSettings(true)}
                                  className="w-full bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-black tracking-wider text-lg py-5 px-6 rounded-2xl shadow-[0_0_30px_rgba(16,185,129,0.3)] transition-all transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-3 border border-emerald-400/50 mt-4"
                                >
                                  <Settings2 className="w-7 h-7"/>
                                  <span className="uppercase">ဗီဒီယို ပြင်ဆင်ရန် / Render လုပ်မည်</span>
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </>
                ) : (
                  <div className="space-y-6 animate-fade-in">
                    <button onClick={() => setShowRenderSettings(false)} className="bg-blue-950/50 hover:bg-blue-900/50 text-cyan-300 px-4 py-2 rounded-xl border border-blue-900/50 flex items-center gap-2 transition-colors font-bold text-sm">
                      <ArrowLeft className="w-4 h-4"/> Back to Audio (ပြန်ပြင်မည်)
                    </button>
                    
                    <div className="bg-[#0a1220]/80 backdrop-blur-xl border border-blue-900/40 rounded-2xl p-6 shadow-2xl space-y-5 hover:border-cyan-500/30 transition-colors">
                      <h3 className="text-lg font-black text-cyan-400 flex items-center gap-2 border-b border-blue-900/40 pb-2 tracking-wide uppercase">
                        ၄။ Visual Effects
                      </h3>
                      <div className="bg-black/50 p-4 rounded-xl border border-blue-900/40 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-bold text-blue-200 flex items-center gap-2 tracking-wide"><Type className="w-4 h-4 text-cyan-500"/> Cinematic Subtitles</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked={enableSubs} onChange={e=>setEnableSubs(e.target.checked)} className="sr-only peer" />
                            <div className="w-9 h-5 bg-blue-950/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-blue-200 after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                          </label>
                        </div>
                        {enableSubs && (
                          <div className="pt-3 border-t border-blue-900/40 space-y-4">
                            <div className="flex items-start gap-2 bg-blue-950/30 p-2 rounded-lg border border-blue-900/50">
                              <Hand className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                              <p className="text-[10.5px] font-bold text-blue-200/80 leading-tight">ညာဘက် Preview ပေါ်ရှိ <span className="text-cyan-500">အပြာရောင်မျဉ်းပြတ်</span> ကို ဖိဆွဲ၍ (Drag/Resize) စာတန်းထိုးနေရာကို ချိန်ညှိပါ။</p>
                            </div>
                            <div className="flex flex-col sm:flex-row gap-3">
                              <div className="flex-1 space-y-2">
                                <span className="text-xs text-blue-200/70 font-bold block uppercase tracking-wider">Text Color -</span>
                                <div className="flex gap-2.5 flex-wrap">
                                  {SUBTITLE_COLORS.map(c => (
                                    <button
                                      key={c.id}
                                      onClick={() => setSubColorObj(c)}
                                      title={c.label}
                                      className={`w-7 h-7 rounded-full border-2 transition-all duration-300 ${subColorObj.id === c.id ? 'scale-125 shadow-[0_0_15px_rgba(255,255,255,0.6)] z-10' : 'border-blue-900/50 hover:scale-110'}`}
                                      style={{ backgroundColor: c.id, borderColor: c.id === '#000000' ? '#ffffff' : (subColorObj.id === c.id ? '#ffffff' : 'transparent') }}
                                    />
                                  ))}
                                </div>
                              </div>
                              <div className="flex-1 space-y-2">
                                <span className="text-xs text-blue-200/70 font-bold block uppercase tracking-wider">Font -</span>
                                <div className="flex items-center gap-2">
                                  <div className="bg-black/60 border border-blue-900/50 rounded-lg px-3 py-2 text-xs font-bold text-blue-100 flex-1 truncate text-center shadow-inner">
                                    {subFont === 'sans-serif' ? 'Default (Sans-serif)' : subFont}
                                  </div>
                                  <label className="bg-blue-950/80 hover:bg-blue-900 border border-cyan-500/50 text-cyan-200 px-3 py-2 rounded-lg cursor-pointer transition-colors text-xs font-bold whitespace-nowrap shadow-sm">
                                    + Font
                                    <input type="file" accept=".ttf,.otf,.woff,.woff2" onChange={handleFontUpload} className="hidden" />
                                  </label>
                                  {subFont !== 'sans-serif' && (
                                    <button
                                      onClick={() => setSubFont('sans-serif')}
                                      className="bg-black/60 hover:bg-blue-950/50 border border-blue-900/50 text-cyan-400 p-2 rounded-lg transition-colors shadow-sm"
                                      title="Reset to Default"
                                    >
                                      <RefreshCw className="w-4 h-4" />
                                    </button>
                                  )}
                                </div>
                              </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-[11px] text-blue-200/70 flex justify-between font-bold mb-1.5 uppercase tracking-wider"><span>Stroke (%)</span> <span className="text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-900/50">{subStroke}</span></label>
                                <input type="range" min="0" max="30" value={subStroke} onChange={e=>setSubStroke(parseInt(e.target.value))} className="w-full accent-cyan-500 h-1.5 bg-blue-950 rounded-lg appearance-none cursor-pointer" />
                              </div>
                              <div>
                                <label className="text-[11px] text-blue-200/70 flex justify-between font-bold mb-1.5 uppercase tracking-wider"><span>Bg Opacity</span> <span className="text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-900/50">{subBgOpacity}%</span></label>
                                <input type="range" min="0" max="100" value={subBgOpacity} onChange={e=>setSubBgOpacity(parseInt(e.target.value))} className="w-full accent-cyan-500 h-1.5 bg-blue-950 rounded-lg appearance-none cursor-pointer" />
                              </div>
                            </div>
                            <div className="space-y-2">
                                <label className="text-[11px] text-blue-200/70 flex justify-between font-bold uppercase tracking-wider"><span>Background Color</span></label>
                                <div className="flex items-center gap-3">
                                   <input type="color" value={subBgColor} onChange={e=>setSubBgColor(e.target.value)} className="w-9 h-9 rounded cursor-pointer border border-blue-900/50 bg-black outline-none p-0.5" />
                                   <div className="flex gap-2 bg-black/40 p-1.5 rounded-lg border border-blue-900/30">
                                      {SUBTITLE_BG_PRESETS.map(color => (
                                         <button key={color} onClick={() => setSubBgColor(color)} title={color} className={`w-6 h-6 rounded-full border border-blue-900/50 transition-all ${subBgColor === color ? 'ring-2 ring-cyan-500 scale-110' : 'hover:scale-110'}`} style={{backgroundColor: color}} />
                                      ))}
                                   </div>
                                </div>
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="bg-black/50 p-4 rounded-xl border border-blue-900/40 space-y-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-bold text-blue-200 flex items-center gap-2 tracking-wide"><Target className="w-4 h-4 text-cyan-500" /> Interactive Blur Area</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked={blurSubtitles} onChange={e=>setBlurSubtitles(e.target.checked)} className="sr-only peer" />
                            <div className="w-9 h-5 bg-blue-950/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-blue-200 after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                          </label>
                        </div>
                        {blurSubtitles && (
                          <div className="space-y-4 pt-3 border-t border-blue-900/40">
                            <div className="flex items-start gap-2 bg-blue-950/30 p-2 rounded-lg border border-blue-900/50">
                              <Hand className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
                              <p className="text-[10.5px] font-bold text-blue-200/80 leading-tight">ညာဘက် Preview ပေါ်ရှိ <span className="text-cyan-500">အပြာရောင်မျဉ်းပြတ်</span> ကို ဖိဆွဲ၍ (Drag/Resize) မိမိစိတ်ကြိုက် ဝါးလိုသောနေရာကို ချိန်ညှိပါ။</p>
                            </div>
                            <div className="pt-1">
                              <label className="text-[11px] text-blue-200/70 flex justify-between font-bold mb-1.5 uppercase tracking-wider"><span>Blur Strength</span> <span className="text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-900/50">{blurStrength} px</span></label>
                              <input type="range" min="1" max="50" value={blurStrength} onChange={e=>setBlurStrength(e.target.value)} className="w-full accent-cyan-500 h-1.5 bg-blue-950 rounded-lg appearance-none cursor-pointer" />
                            </div>
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col gap-4">
                        <div className="flex items-center justify-between bg-black/50 p-3.5 rounded-xl border border-blue-900/40 shadow-sm">
                          <span className="text-sm font-bold text-blue-200 tracking-wide">Flip Video (Copyright)</span>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked={bypassCopyright} onChange={e=>setBypassCopyright(e.target.checked)} className="sr-only peer" />
                            <div className="w-9 h-5 bg-blue-950/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-blue-200 after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                          </label>
                        </div>
                        <div className="bg-black/50 p-4 rounded-xl border border-blue-900/40 space-y-3">
                          <span className="text-sm font-bold text-blue-200 block tracking-wide">Video Color Tone (Filter)</span>
                          <select
                            value={colorTone}
                            onChange={e=>setColorTone(e.target.value)}
                            className="w-full bg-black border border-blue-900/50 rounded-lg px-3 py-2.5 text-xs font-bold outline-none focus:border-cyan-500 cursor-pointer text-blue-100"
                          >
                            {COLOR_TONES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
                          </select>
                        </div>
                        <div className="bg-black/50 p-4 rounded-xl border border-blue-900/40 space-y-3">
                          <span className="text-sm font-bold text-blue-200 block tracking-wide">Export Settings</span>
                          <div>
                            <label className="text-xs font-bold text-blue-200/70 mb-2 block tracking-wider">Aspect Ratio</label>
                            <div className="flex gap-3">
                              {['16:9', '9:16', '1:1'].map((ratio) => (
                                <button
                                  key={ratio}
                                  onClick={() => setAspectRatio(ratio)}
                                  className={`flex-1 py-2 px-3 rounded-lg text-sm font-bold transition-all border flex items-center justify-center gap-2 ${aspectRatio === ratio  ? 'bg-blue-900/40 border-cyan-500 text-white shadow-[0_0_10px_rgba(6,182,212,0.2)]'  : 'bg-[#0a1220] border-blue-900/30 text-blue-200/50 hover:bg-blue-900/30 hover:text-blue-200' }`}
                                >
                                  {aspectRatio === ratio && <Check className="w-4 h-4" />}
                                  {ratio}
                                </button>
                              ))}
                            </div>
                          </div>
                        </div>

                        <div className="bg-black/50 p-4 rounded-xl border border-blue-900/40 space-y-3">
                            <div className="flex items-center justify-between">
                              <span className="text-sm font-bold text-blue-200 flex items-center gap-2 tracking-wide"><ImageIcon className="w-4 h-4 text-cyan-500" /> Smart Zoom/Fill (No Black Bars)</span>
                              <label className="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" checked={enableZoomCrop} onChange={e=>setEnableZoomCrop(e.target.checked)} className="sr-only peer" />
                                <div className="w-9 h-5 bg-blue-950/50 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-blue-200 after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-cyan-500"></div>
                              </label>
                            </div>
                            {enableZoomCrop && (
                                <div className="pt-3 border-t border-blue-900/40 space-y-4">
                                    <div>
                                      <label className="text-[11px] text-blue-200/70 flex justify-between font-bold mb-1.5 uppercase tracking-wider"><span>Zoom Scale</span> <span className="text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-900/50">{videoScale.toFixed(1)}x</span></label>
                                      <input type="range" min="1.0" max="3.0" step="0.1" value={videoScale} onChange={e=>setVideoScale(parseFloat(e.target.value))} className="w-full accent-cyan-500 h-1.5 bg-blue-950 rounded-lg appearance-none cursor-pointer" />
                                    </div>
                                    <div>
                                      <label className="text-[11px] text-blue-200/70 flex justify-between font-bold mb-1.5 uppercase tracking-wider"><span>Vertical Position (Pan Y)</span> <span className="text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-900/50">{videoPanY}</span></label>
                                      <input type="range" min="-100" max="100" step="1" value={videoPanY} onChange={e=>setVideoPanY(parseInt(e.target.value))} className="w-full accent-cyan-500 h-1.5 bg-blue-950 rounded-lg appearance-none cursor-pointer" />
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="flex flex-col gap-2 bg-gradient-to-r from-blue-950/50 to-black/50 p-4 rounded-xl border border-blue-900/50 shadow-inner group transition-all hover:border-cyan-500/50 relative overflow-hidden">
                          <div className="absolute -right-4 -top-4 opacity-5 group-hover:opacity-10 transition-opacity">
                            <Zap className="w-24 h-24 text-cyan-500" />
                          </div>
                          <div className="flex items-center justify-between relative z-10">
                            <div>
                              <span className="text-sm font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 flex items-center gap-2 tracking-wide uppercase">
                                <Zap className="w-4 h-4 text-cyan-500" /> Hyper-Sync AI (Auto-Stretch)
                              </span>
                              <p className="text-[10px] text-blue-200/60 mt-1 font-bold">Automatically adjust video playback speed elastically to match the audio narration perfectly.</p>
                            </div>
                            <label className="relative inline-flex items-center cursor-pointer ml-4 shrink-0">
                              <input type="checkbox" checked={hyperSync} onChange={e=>setHyperSync(e.target.checked)} className="sr-only peer" />
                              <div className="w-11 h-6 bg-blue-950/80 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-blue-200 after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gradient-to-r peer-checked:from-blue-600 peer-checked:to-cyan-500 shadow-[0_0_10px_rgba(0,0,0,0.5)]"></div>
                            </label>
                          </div>
                        </div>
                        <div className="bg-black/50 p-4 rounded-xl border border-blue-900/40 space-y-4">
                          <span className="text-sm font-bold text-blue-200 block tracking-wide">Studio Watermark (Logo)</span>
                          <div className="flex flex-col sm:flex-row items-center gap-3">
                            <input type="file" accept="image/*" onChange={handleLogoUpload} className="hidden" id="logo-upload" />
                            <label htmlFor="logo-upload" className="w-full sm:flex-1 p-2.5 border border-dashed border-blue-900/50 rounded-lg cursor-pointer hover:border-cyan-500 hover:bg-blue-950/20 transition-colors text-center text-xs font-bold text-cyan-400 uppercase tracking-widest">
                              {logoFile ? <span className="text-cyan-300">{logoFile.name}</span> : "+ Upload Logo"}
                            </label>
                            <select value={logoPos} onChange={e=>setLogoPos(e.target.value)} className="w-full sm:w-auto bg-black border border-blue-900/50 rounded-lg px-3 py-2.5 text-xs font-bold outline-none focus:border-cyan-500 cursor-pointer text-blue-100">
                              {LOGO_POSITIONS.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                            </select>
                          </div>
                          {logoUrl && (
                            <div className="pt-3 border-t border-blue-900/40 grid grid-cols-2 gap-4">
                              <div>
                                <label className="text-[11px] text-blue-200/70 flex justify-between font-bold mb-1.5 uppercase tracking-wider"><span>Size (%)</span> <span className="text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-900/50">{logoSize}</span></label>
                                <input type="range" min="5" max="50" value={logoSize} onChange={e=>setLogoSize(parseInt(e.target.value))} className="w-full accent-cyan-500 h-1.5 bg-blue-950 rounded-lg appearance-none cursor-pointer" />
                              </div>
                              <div>
                                <label className="text-[11px] text-blue-200/70 flex justify-between font-bold mb-1.5 uppercase tracking-wider"><span>Opacity (%)</span> <span className="text-cyan-400 bg-blue-950 px-2 py-0.5 rounded border border-blue-900/50">{logoOpacity}</span></label>
                                <input type="range" min="10" max="100" value={logoOpacity} onChange={e=>setLogoOpacity(parseInt(e.target.value))} className="w-full accent-cyan-500 h-1.5 bg-blue-950 rounded-lg appearance-none cursor-pointer" />
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => handleRenderFinalVideo()}
                      disabled={isRendering}
                      className="w-full bg-gradient-to-r from-emerald-600 to-cyan-600 hover:from-emerald-500 hover:to-cyan-500 text-white font-black tracking-wider text-lg py-5 px-6 rounded-2xl shadow-[0_0_30px_rgba(16,185,129,0.3)] transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 flex flex-col items-center justify-center gap-2 border border-emerald-400/50 mt-4"
                    >
                       <div className="flex items-center gap-3">
                          {isRendering ? <Loader2 className="w-7 h-7 animate-spin"/> : <DownloadCloud className="w-7 h-7"/>}
                          <span className="uppercase">{isRendering ? "Rendering..." : "Start Export Rendering (ဗီဒီယို အပြီးသတ် ထုတ်ယူမည်)"}</span>
                       </div>
                    </button>
                  </div>
                )}
              </div>

              {/* RIGHT PANEL - LIVE PREVIEW & RESULTS (Hidden during Script/Audio Phase) */}
              <div className={showRenderSettings ? "xl:col-span-7 space-y-6 order-1 xl:order-2 animate-fade-in" : "hidden"}>
                <div className="bg-[#0a1220]/90 border border-blue-900/40 rounded-2xl p-4 shadow-2xl relative min-h-[500px] flex flex-col items-center justify-center overflow-hidden sticky top-8">
                  {!videoUrl ? (
                    <div className="text-blue-900/40 flex flex-col items-center text-center p-8 animate-pulse">
                      <Film className="w-24 h-24 mb-4 text-blue-900/50" />
                      <p className="font-black text-2xl text-cyan-500/50 tracking-widest uppercase">Director's Monitor</p>
                      <p className="text-sm mt-3 font-medium max-w-sm text-blue-200/30">Upload a video to access the live preview monitor.</p>
                    </div>
                  ) : (
                    <div className="w-full flex flex-col items-center">
                      <div className="relative w-full rounded-xl overflow-hidden bg-black flex justify-center items-center shadow-[0_0_40px_rgba(0,0,0,0.9)] group border border-blue-900/30">
                        <video
                          ref={videoRef}
                          src={videoUrl}
                          crossOrigin="anonymous"
                          playsInline
                          muted
                          className="hidden"
                          onLoadedMetadata={(e) => {
                            setVideoDurationSeconds(e.target.duration);
                            e.target.currentTime = 0.1; 
                          }}
                        />
                        {generatedAudioUrl && <audio ref={audioRef} src={generatedAudioUrl} className="hidden" onLoadedMetadata={e => setAudioDuration(e.target.duration)} onTimeUpdate={handleAudioTimeUpdate} onEnded={() => setIsPreviewPlaying(false)} />}
                        
                        <div className="relative w-full flex justify-center items-center overflow-hidden" style={{
                          aspectRatio: aspectRatio === '16:9' ? '16/9' : aspectRatio === '9:16' ? '9/16' : '1/1',
                          maxHeight: '600px'
                        }}>
                          <canvas
                            ref={canvasRef}
                            className={`w-full h-full object-contain bg-black ${!isRendering ? 'cursor-move touch-none' : ''}`}
                            onMouseDown={handlePointerDown}
                            onMouseMove={handlePointerMove}
                            onMouseUp={handlePointerUp}
                            onMouseLeave={handlePointerUp}
                            onTouchStart={handlePointerDown}
                            onTouchMove={handlePointerMove}
                            onTouchEnd={handlePointerUp}
                          />
                        </div>

                        {!generatedAudioUrl && !isRendering && (
                          <div className="absolute top-4 left-4 bg-black/80 backdrop-blur-md px-4 py-2 rounded-lg border border-blue-900/50 text-[10px] font-black tracking-widest flex items-center gap-2 shadow-lg pointer-events-none text-cyan-500 uppercase">
                            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 animate-pulse shadow-[0_0_10px_rgba(6,182,212,0.8)]"></span> LIVE MONITOR
                          </div>
                        )}

                        {generatedAudioUrl && !isRendering && !finalVideoUrl && !isPreviewPlaying && (
                          <div className="absolute inset-0 bg-black/80 backdrop-blur-sm flex flex-col items-center justify-center p-6 text-center animate-fade-in opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                            <Film className="w-16 h-16 text-cyan-500 mb-3" />
                            <h3 className="text-3xl font-black text-white mb-2 tracking-wide uppercase">Audio Ready</h3>
                            <div className="flex flex-col items-center gap-2 mb-6">
                              <p className="text-cyan-300 text-sm font-bold flex items-center justify-center gap-2 bg-blue-950/60 px-5 py-2 rounded-full border border-blue-900/50 tracking-wider">
                                <Clock className="w-4 h-4"/> Duration: {formatTime(audioDuration)}
                              </p>
                              {hyperSync && audioDuration > 0 && videoDurationSeconds > 0 && (
                                <p className="text-blue-400 text-[10px] font-black tracking-widest uppercase flex items-center gap-1">
                                  <Zap className="w-3 h-3" /> Stretch: {(videoDurationSeconds / audioDuration).toFixed(2)}x
                                </p>
                              )}
                            </div>
                            
                            <div className="flex flex-col sm:flex-row gap-4 w-full justify-center flex-wrap">
                              <button onClick={togglePreviewPlay} className="flex-1 bg-black/60 hover:bg-blue-950/40 border border-blue-900/50 text-white font-bold py-3.5 px-5 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg uppercase tracking-wide">
                                <Play className="w-5 h-5 text-cyan-500"/> Play
                              </button>
                              <button onClick={downloadSRT} className="flex-1 bg-black/60 hover:bg-blue-950/40 border border-blue-900/50 text-white font-bold py-3.5 px-5 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg uppercase tracking-wide">
                                <DownloadCloud className="w-5 h-5 text-cyan-500"/> Get SRT
                              </button>
                            </div>
                          </div>
                        )}

                        {isRendering && (
                          <div className="absolute inset-0 bg-black/95 backdrop-blur-md flex flex-col items-center justify-center p-8 animate-fade-in z-50">
                            <div className="w-full max-w-md space-y-6 text-center">
                              <h4 className="text-cyan-500 font-black text-2xl animate-pulse tracking-widest uppercase">Rendering Cut...</h4>
                              <div className="h-4 bg-blue-950/30 rounded-full overflow-hidden border border-blue-900/50 shadow-inner p-0.5">
                                <div className="h-full bg-gradient-to-r from-blue-700 via-cyan-500 to-blue-500 rounded-full transition-all duration-300 ease-out" style={{width: `${renderProgress}%`}}></div>
                              </div>
                              <p className="text-white font-mono text-2xl font-black">{Math.floor(renderProgress)}%</p>
                              <p className="text-xs font-bold text-cyan-400 mt-2 bg-blue-950/40 p-3 rounded-lg inline-block border border-blue-900/50 tracking-wide leading-relaxed">
                                <AlertTriangle className="w-4 h-4 inline mr-1 -mt-0.5" />
                                Please keep this window open while rendering. Do not switch tabs.
                              </p>
                            </div>
                          </div>
                        )}

                        {finalVideoUrl && (
                          <div className="absolute inset-0 bg-black/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center animate-fade-in z-50">
                            <div className="w-24 h-24 bg-blue-900/30 rounded-full flex items-center justify-center mb-6 shadow-[0_0_30px_rgba(6,182,212,0.2)]">
                              <Film className="w-12 h-12 text-cyan-500" />
                            </div>
                            <h3 className="text-4xl font-black text-white mb-8 tracking-tighter uppercase text-transparent bg-clip-text bg-gradient-to-b from-white to-blue-200">Director's Cut Ready</h3>
                            <div className="flex flex-col sm:flex-row gap-4 w-full max-w-md">
                              <button onClick={()=>{setFinalVideoUrl(null); setIsRendering(false);}} className="flex-1 bg-black/50 border border-blue-900/50 hover:bg-blue-950/30 text-blue-100 font-bold py-4 px-4 rounded-xl transition-colors shadow-lg flex justify-center items-center gap-2 uppercase text-sm tracking-wide">
                                <RefreshCw className="w-4 h-4"/> Remake
                              </button>
                              <button onClick={downloadFinalVideo} className="flex-[2] bg-gradient-to-r from-blue-600 to-blue-800 hover:from-blue-500 hover:to-blue-700 text-white font-black py-4 px-4 rounded-xl shadow-[0_0_30px_rgba(6,182,212,0.5)] transition-transform hover:scale-105 flex items-center justify-center gap-2 text-lg uppercase tracking-wider border border-cyan-500/50">
                                <Download className="w-6 h-6"/> Save Video (.{exportExt})
                              </button>
                            </div>
                          </div>
                        )}
                      </div>

                      {(videoUrl || generatedAudioUrl) && !isRendering && !finalVideoUrl && renderMiniPlayer()}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <style dangerouslySetInnerHTML={{__html: `@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Myanmar:wght@400;500;700;900&display=swap'); .font-mm { font-family: 'Pyidaungsu', 'Myanmar Text', 'Noto Sans Myanmar', sans-serif; } @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } } @keyframes fade-in-up { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } } .animate-fade-in { animation: fade-in 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; } .animate-fade-in-up { animation: fade-in-up 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }`}} />
    </div>
  );
}
```

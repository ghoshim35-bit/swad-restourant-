# 🎬 YouTube AI Agent

Ek AI agent jisse aap normal baat karke (Hindi / Hinglish / English) apna YouTube channel chala sakte hain.
Andar Claude (Anthropic) ka AI hai, aur yeh YouTube Data API ke through aapke channel par kaam karta hai.

## Yeh kya kya kar sakta hai

| Kaam | Example bolkar dekhiye |
|---|---|
| Trending topics dekhna (apni video ke ideas ke liye) | "aaj India mein kya trend kar raha hai? mere liye 5 video ideas do" |
| Video upload (title, description, tags AI khud likhega) | "videos folder ki video upload karo, cooking channel hai" |
| Upload schedule karna | "kal shaam 6 baje publish ho aisa schedule karo" |
| Thumbnail lagana | "video abc123 par thumb.jpg thumbnail lagao" |
| Videos aur views/likes dekhna | "meri last 10 videos ke views dikhao" |
| Title / description / tags badalna | "sabse kam views wali video ka title better banao" |
| Private / unlisted / public karna | "video abc123 public kar do" |
| Comments padhna aur reply karna | "latest video ke comments ka achha sa reply karo" |
| Video delete karna | "video abc123 delete karo" |

**Copyright:** Trending list sirf ideas ke liye hai. Doosron ki video download karke re-upload mat kijiye.
Usse copyright strike aati hai aur 3 strikes par channel delete ho jata hai. Sirf apni banayi hui videos upload kijiye.

**Safety:** Upload, delete, public karna aur comment reply karne se pehle agent aapse `y/n` poochhega.
Aap `n` likhenge to woh kaam nahi hoga. Videos default roop se **private** upload hoti hain.

## Setup (sirf ek baar)

### 1. Python install karein
Python 3.10 ya usse naya: https://www.python.org/downloads/

### 2. Libraries install karein
```bash
cd YouTube/agent
pip install -r requirements.txt
```

### 3. Claude API key
1. https://console.anthropic.com par account banaiye aur **API Keys** mein nayi key banaiye.
2. Terminal mein set kijiye:
   - Mac/Linux: `export ANTHROPIC_API_KEY="aapki-key"`
   - Windows (PowerShell): `$env:ANTHROPIC_API_KEY="aapki-key"`

### 4. YouTube API access (Google Cloud)
1. https://console.cloud.google.com par jaakar ek naya project banaiye.
2. **APIs & Services → Library** mein "YouTube Data API v3" search karke **Enable** kijiye.
3. **APIs & Services → OAuth consent screen**: "External" chuniye, app ka naam bhariye,
   aur **Test users** mein apna Gmail (jis par YouTube channel hai) add kijiye.
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID** →
   Application type: **Desktop app** → Create → **Download JSON**.
5. Download hui file ka naam `client_secret.json` rakhkar is `agent` folder mein daal dijiye.

> ⚠️ `client_secret.json` aur `token.json` secret hain. Inhe kabhi GitHub par upload mat kijiye
> (`.gitignore` already inhe rok deta hai).

## Free mode (bina Claude API key ke)

Pehle free mein try karna ho to Step 3 (Claude API key) chhod dijiye aur yeh chalaiye:

```bash
python free_mode.py
```

Yeh menu wala mode hai: channel info, trending ideas, apni videos/views, upload, title badalna, comments.
YouTube API free hai, isliye iska koi kharcha nahi. Bas title/description/tags aapko khud likhne honge.
AI (Claude) se likhwana ho to neeche wala `youtube_agent.py` chalaiye.

## Chalana

```bash
cd YouTube/agent
python youtube_agent.py
```

Pehli baar YouTube ka koi kaam karne par browser khulega. Wahan apne channel wale Google account se login karke
**Allow** kijiye. Uske baad login `token.json` mein save rehta hai.

Agar ek Google account mein kai channels hain, to Google login ke waqt **sahi channel** (jaise `@yuvikaThakur1812`) chuniye.
Login ke baad agent `✅ Connected channel: ...` dikhayega, taaki aap check kar sakein. Galat channel connect ho jaye to
`token.json` delete karke dobara login kijiye. Kabhi bhi poochh sakte hain: "kaunsa channel connected hai?"

Apni videos `YouTube/agent/videos/` folder mein rakh sakte hain (yeh folder git mein nahi jata), phir agent ko boliye:
"videos folder ki video upload karo".

## Dhyan rakhne wali baatein

- YouTube API ka free quota roz ~10,000 units hai. Ek upload lagbhag 1,600 units leta hai,
  matlab roz takreeban 6 uploads.
- Jab tak Google aapke app ko verify nahi karta, API se upload hui videos YouTube **private** bhi rakh sakta hai.
  Apne khud ke channel ke liye "Testing" mode kaafi hai.
- Custom thumbnail ke liye channel verified hona chahiye (YouTube Studio mein phone number se verify hota hai).
- Claude API ka kharcha aapke Anthropic account se kat-ta hai.

## Files

- `youtube_agent.py` - AI agent (chat loop + tools)
- `free_mode.py` - bina AI ka free menu mode
- `youtube_api.py` - YouTube API ke functions (login, upload, update, comments...)
- `requirements.txt` - zaroori Python libraries

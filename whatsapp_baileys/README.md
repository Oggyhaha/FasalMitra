# 🌾 FasalMitra Baileys WhatsApp Bot

A lightweight, multi-device WhatsApp AI gateway built with [WhiskeySockets/Baileys](https://github.com/WhiskeySockets/Baileys) and connected directly to the FasalMitra FastAPI backend.

---

## 🚀 Quick Start Guide

### Step 1: Ensure FasalMitra Backend is Running
In one terminal window, start your FastAPI backend:
```bash
uvicorn backend.app.main:app --reload --port 8000
```

### Step 2: Start the WhatsApp Bot
In another terminal window:
```bash
cd whatsapp_baileys
npm start
```

### Step 3: Link Your WhatsApp Account
1. The terminal will display a QR code.
2. Open WhatsApp on your phone (use a test/secondary SIM card).
3. Go to **Settings** (or tap the 3 dots on Android) -> **Linked Devices** -> **Link a Device**.
4. Scan the QR code shown in your terminal.
5. Once scanned, the terminal will confirm:
   ```
   ✅ SUCCESS: FASALMITRA WHATSAPP BOT IS CONNECTED & ACTIVE!
   ```

---

## 📱 How It Works

1. **Farmer Asks a Question on WhatsApp:**
   A farmer sends any query via WhatsApp text (in Marathi, Hindi, Gujarati, or English):
   > *"सोयाबीनवर चक्रीभुंग्याचा प्रादुर्भाव झाला आहे, काय उपाय करावा?"*
2. **Bot Sends Typing Indicator:**
   The bot automatically shows the WhatsApp typing indicator (`typing...`) to simulate a natural assistant.
3. **FasalMitra Cognitive Pipeline:**
   The bot calls `POST http://localhost:8000/api/v1/webhooks/whatsapp/json`. FasalMitra retrieves verified ICAR evidence and generates grounded advice.
4. **Instant Text Advisory:**
   The bot replies with the grounded diagnosis, dosages, and safety precautions.
5. **Native Voice Note (PTT):**
   The bot sends an audio voice note directly into the chat with native WhatsApp audio waveform!

---

## ⚠️ Important Precautions for Testing
- **Do NOT use your primary personal phone number.** Always use a secondary, test, or office SIM card.
- **Reply-only mode:** The bot only replies when a user sends a message first. Do not send unsolicited bulk broadcasts.
- **Session Reset:** If you ever need to link a new phone number, delete the `auth_info_baileys` folder and run `npm start` again.

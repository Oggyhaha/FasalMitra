import makeWASocket, {
    DisconnectReason,
    useMultiFileAuthState,
    fetchLatestBaileysVersion
} from '@whiskeysockets/baileys';
import qrcode from 'qrcode-terminal';
import pino from 'pino';
import axios from 'axios';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000/api/v1/webhooks/whatsapp/json';
const AUTH_DIR = path.resolve(__dirname, 'auth_info_baileys');

console.log('🌾 ========================================================');
console.log('🌾   FASALMITRA (फसलमित्र) - WHATSAPP AI ASSISTANT BOT    ');
console.log('🌾   Powered by Baileys Multi-Device WebSocket Gateway    ');
console.log('🌾 ========================================================');
console.log(`🔗 Connected Backend API: ${FASTAPI_URL}`);

// Set to keep track of processed message IDs to prevent duplicates
const processedMessageIds = new Set();

async function connectToWhatsApp() {
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version, isLatest } = await fetchLatestBaileysVersion();

    console.log(`📦 Using Baileys WhatsApp Web Version: ${version.join('.')} (isLatest: ${isLatest})`);

    const sock = makeWASocket({
        version,
        logger: pino({ level: 'silent' }), // Suppress noisy protocol logs
        printQRInTerminal: false,
        auth: state,
        browser: ['FasalMitra AI', 'Desktop', '2.0.0'],
        syncFullHistory: false
    });

    sock.ev.on('creds.update', saveCreds);

    sock.ev.on('connection.update', async (update) => {
        const { connection, lastDisconnect, qr } = update;

        if (qr) {
            console.log('\n========================================================');
            console.log('📲 SCAN THIS QR CODE WITH YOUR WHATSAPP TO CONNECT:');
            console.log('========================================================\n');
            qrcode.generate(qr, { small: true });
            console.log('\n📋 INSTRUCTIONS:');
            console.log('1. Open WhatsApp on your phone (use test/secondary SIM)');
            console.log('2. Tap Settings (iOS) or 3 Dots (Android) -> Linked Devices');
            console.log('3. Tap "Link a Device" and point camera at the QR code above.');
            console.log('========================================================\n');
        }

        if (connection === 'close') {
            const statusCode = (lastDisconnect?.error)?.output?.statusCode;
            const shouldReconnect = statusCode !== DisconnectReason.loggedOut;

            console.log(`⚠️ Connection closed (statusCode: ${statusCode}). Reconnecting: ${shouldReconnect}`);

            if (shouldReconnect) {
                setTimeout(() => connectToWhatsApp(), 3000);
            } else {
                console.log('❌ Device logged out. To re-link, delete the "auth_info_baileys" folder and restart.');
            }
        } else if (connection === 'open') {
            console.log('\n🌾 ========================================================');
            console.log('✅ SUCCESS: FASALMITRA WHATSAPP BOT IS CONNECTED & ACTIVE!');
            console.log('   Ready to receive farmer questions in Marathi, Hindi, Gujarati, English.');
            console.log('🌾 ========================================================\n');
        }
    });

    sock.ev.on('messages.upsert', async (m) => {
        if (m.type !== 'notify') return;

        for (const msg of m.messages) {
            // Ignore messages sent by the bot itself
            if (msg.key.fromMe) continue;

            const remoteJid = msg.key.remoteJid;
            // Ignore status broadcasts and group messages unless desired
            if (!remoteJid || remoteJid.includes('@broadcast') || remoteJid.includes('status@broadcast')) {
                continue;
            }

            const messageId = msg.key.id;
            if (processedMessageIds.has(messageId)) continue;
            processedMessageIds.add(messageId);

            // Clean cache periodically
            if (processedMessageIds.size > 2000) {
                processedMessageIds.clear();
            }

            // Extract sender text
            const userText = msg.message?.conversation ||
                             msg.message?.extendedTextMessage?.text ||
                             msg.message?.imageMessage?.caption ||
                             '';

            if (!userText || !userText.trim()) continue;

            const senderPhone = '+' + remoteJid.replace('@s.whatsapp.net', '').replace('@c.us', '');
            const now = new Date().toLocaleTimeString();

            console.log(`\n[${now}] 📩 [NEW WHATSAPP MESSAGE] From ${senderPhone}: "${userText.trim()}"`);

            try {
                // 1. Simulate typing indicator on WhatsApp
                await sock.sendPresenceUpdate('composing', remoteJid);

                // 2. Query FasalMitra FastAPI Advisory Pipeline
                const response = await axios.post(FASTAPI_URL, {
                    phone: senderPhone,
                    message: userText.trim(),
                    language: 'auto',
                    district: 'Latur'
                }, { timeout: 35000 });

                // 3. Stop typing indicator
                await sock.sendPresenceUpdate('paused', remoteJid);

                const data = response.data;
                const replyText = data.reply_body || "नमस्कार! आपल्या प्रश्नावर सल्ला तयार करण्यात आला आहे.";

                // 4. Send Grounded Text Advisory Reply
                await sock.sendMessage(remoteJid, { text: replyText }, { quoted: msg });
                console.log(`[${now}] 🚀 [REPLY SENT] To ${senderPhone}`);

                // 5. Send Audio Voice Note (PTT) if available
                const audioUrl = data.audio_url || data.pipeline_result?.audio_url;
                if (audioUrl) {
                    const audioFilename = path.basename(audioUrl);
                    const localAudioPath = path.resolve(__dirname, '..', 'static', 'audio', audioFilename);

                    if (fs.existsSync(localAudioPath)) {
                        console.log(`[${now}] 🎙️ [SENDING VOICE NOTE] ${localAudioPath}...`);
                        const audioBuffer = fs.readFileSync(localAudioPath);
                        await sock.sendMessage(remoteJid, {
                            audio: audioBuffer,
                            mimetype: 'audio/mp4',
                            ptt: true // WhatsApp native voice note waveform!
                        }, { quoted: msg });
                        console.log(`[${now}] ✅ [VOICE NOTE DELIVERED] To ${senderPhone}`);
                    }
                }
            } catch (err) {
                console.error(`[${now}] ❌ Error processing message from ${senderPhone}:`, err.message);
                await sock.sendPresenceUpdate('paused', remoteJid);
                try {
                    await sock.sendMessage(remoteJid, {
                        text: "🙏 दिलगीर आहोत, सर्व्हरशी संपर्क करताना त्रुटी आली. कृपया थोड्या वेळाने पुन्हा प्रयत्न करा."
                    }, { quoted: msg });
                } catch (sendErr) {
                    // Ignore send error
                }
            }
        }
    });

    return sock;
}

// Start the WhatsApp Gateway
connectToWhatsApp().catch(err => {
    console.error('Fatal initialization error:', err);
});

import makeWASocket, {
    DisconnectReason,
    useMultiFileAuthState,
    fetchLatestBaileysVersion,
    downloadMediaMessage
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
console.log('🌾   FASALMITRA (फसलमित्र) - MULTIMODAL WHATSAPP BOT      ');
console.log('🌾   Supports Text & Real Voice Note (Audio) Input/Output ');
console.log('🌾 ========================================================');
console.log(`🔗 Connected Backend API: ${FASTAPI_URL}`);

// Set to keep track of processed message IDs to prevent duplicates
const processedMessageIds = new Set();

// If --clean flag passed or explicitly requested, clear old session before starting
if (process.argv.includes('--clean') || process.env.CLEAN_AUTH === 'true') {
    if (fs.existsSync(AUTH_DIR)) {
        console.log('🧹 Clearing previous WhatsApp auth session for a fresh QR scan...');
        try {
            fs.rmSync(AUTH_DIR, { recursive: true, force: true });
        } catch (e) {}
    }
}

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
            console.log('1. Open WhatsApp on your phone');
            console.log('2. Tap Settings (iOS) or 3 Dots (Android) -> Linked Devices');
            console.log('3. Tap "Link a Device" and point camera at the QR code above.');
            console.log('========================================================\n');
        }

        if (connection === 'close') {
            const statusCode = (lastDisconnect?.error)?.output?.statusCode;
            const isLoggedOut = statusCode === DisconnectReason.loggedOut || statusCode === 401;

            if (isLoggedOut) {
                console.log(`\n🔄 Device logged out from phone (statusCode: ${statusCode}). Auto-resetting session...`);
                try {
                    if (fs.existsSync(AUTH_DIR)) {
                        fs.rmSync(AUTH_DIR, { recursive: true, force: true });
                    }
                } catch (rmErr) {
                    console.error('Error clearing auth dir:', rmErr.message);
                }
                console.log('📲 Generating a brand new QR Code scanner in 2 seconds...\n');
                setTimeout(() => connectToWhatsApp(), 2000);
            } else {
                console.log(`⚠️ Connection closed (statusCode: ${statusCode}). Reconnecting in 3 seconds...`);
                setTimeout(() => connectToWhatsApp(), 3000);
            }
        } else if (connection === 'open') {
            console.log('\n🌾 ========================================================');
            console.log('✅ SUCCESS: FASALMITRA WHATSAPP BOT IS CONNECTED & ACTIVE!');
            console.log('   Ready for both TEXT messages and VOICE NOTES (Audio Mic)!');
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

            const senderPhone = '+' + remoteJid.replace('@s.whatsapp.net', '').replace('@c.us', '');
            const now = new Date().toLocaleTimeString();

            // 1. Check for Text Query
            let userText = msg.message?.conversation ||
                           msg.message?.extendedTextMessage?.text ||
                           msg.message?.imageMessage?.caption ||
                           '';

            // 2. Check for Voice Message (Farmer speaking into the mic)
            let audioBase64 = null;
            const isVoiceNote = !!(msg.message?.audioMessage);

            if (isVoiceNote) {
                try {
                    console.log(`\n[${now}] 🎙️ [INCOMING VOICE NOTE DETECTED] From ${senderPhone}...`);
                    const audioBuffer = await downloadMediaMessage(msg, 'buffer', {});
                    audioBase64 = audioBuffer.toString('base64');
                    console.log(`[${now}] 🎙️ [AUDIO DOWNLOADED] ${audioBuffer.length} bytes received`);
                } catch (downloadErr) {
                    console.error(`[${now}] ❌ Failed to download audio media:`, downloadErr.message);
                }
            }

            // Skip if no text and no audio
            if (!userText.trim() && !audioBase64) continue;

            if (userText.trim()) {
                console.log(`\n[${now}] 📩 [NEW TEXT MESSAGE] From ${senderPhone}: "${userText.trim()}"`);
            }

            try {
                // Show typing / recording presence on WhatsApp
                await sock.sendPresenceUpdate(isVoiceNote ? 'recording' : 'composing', remoteJid);

                // Send request to FasalMitra FastAPI Backend
                const response = await axios.post(FASTAPI_URL, {
                    phone: senderPhone,
                    message: userText.trim(),
                    audio_base64: audioBase64,
                    language: 'auto',
                    district: 'Latur'
                }, { timeout: 45000 });

                await sock.sendPresenceUpdate('paused', remoteJid);

                const data = response.data;
                const replyText = data.reply_body || "नमस्कार! आपल्या प्रश्नावर सल्ला तयार करण्यात आला आहे.";

                // 1. Send Grounded Text Advisory Reply
                await sock.sendMessage(remoteJid, { text: replyText }, { quoted: msg });
                console.log(`[${now}] 🚀 [TEXT REPLY SENT] To ${senderPhone}`);

                // 2. Send Native Voice Note (PTT Waveform) if available
                const audioUrl = data.audio_url || data.pipeline_result?.audio_url;
                if (audioUrl) {
                    const audioFilename = path.basename(audioUrl);
                    const oggFilename = audioFilename.replace(/\.mp3$/i, '.ogg');
                    const localOggPath = path.resolve(__dirname, '..', 'static', 'audio', oggFilename);
                    const localMp3Path = path.resolve(__dirname, '..', 'static', 'audio', audioFilename);

                    // A) Native WhatsApp Voice Note requires OGG Opus format
                    if (fs.existsSync(localOggPath)) {
                        console.log(`[${now}] 🎙️ [SENDING NATIVE OGG VOICE NOTE] ${localOggPath}...`);
                        const oggBuffer = fs.readFileSync(localOggPath);
                        await sock.sendMessage(remoteJid, {
                            audio: oggBuffer,
                            mimetype: 'audio/ogg; codecs=opus',
                            ptt: true // Real WhatsApp voice note waveform player!
                        }, { quoted: msg });
                        console.log(`[${now}] ✅ [VOICE NOTE DELIVERED] To ${senderPhone}`);
                    }
                    // B) Fallback: Standard MP3 audio track (ptt: false so WhatsApp won't fail with corrupt player)
                    else if (fs.existsSync(localMp3Path)) {
                        console.log(`[${now}] 🎵 [SENDING MP3 AUDIO] ${localMp3Path}...`);
                        const mp3Buffer = fs.readFileSync(localMp3Path);
                        await sock.sendMessage(remoteJid, {
                            audio: mp3Buffer,
                            mimetype: 'audio/mpeg',
                            ptt: false
                        }, { quoted: msg });
                        console.log(`[${now}] ✅ [MP3 AUDIO DELIVERED] To ${senderPhone}`);
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

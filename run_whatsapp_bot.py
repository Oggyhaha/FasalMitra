import asyncio
import os
import sys
import httpx
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".whatsapp_session"))

async def start_whatsapp_bot():
    print("=" * 75, flush=True)
    print("🌾 FASALMITRA -- REAL-TIME AUTOMATED WHATSAPP WEB AI BOT GATEWAY", flush=True)
    print("   Connected to FastAPI Backend & Live Supabase PostgreSQL Database", flush=True)
    print("=" * 75, flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        page = await browser.new_page()
        await page.goto("https://web.whatsapp.com")

        print("⏳ Waiting for WhatsApp Web chat list to load...", flush=True)
        try:
            await page.wait_for_selector("#pane-side, div[role='grid']", timeout=120000)
            print("✅ SUCCESS: WhatsApp Web Chat List Loaded & Active!", flush=True)
        except Exception:
            print("Please scan the QR code if visible on screen...", flush=True)
            await page.wait_for_selector("#pane-side, div[role='grid']", timeout=180000)

        print("🤖 FasalMitra AI Bot is actively watching for incoming WhatsApp messages...\n", flush=True)
        processed_msg_ids = set()

        while True:
            try:
                now_str = datetime.now().strftime("%H:%M:%S")

                # 1. ALWAYS CHECK CURRENTLY OPEN ACTIVE CHAT WINDOW (#main) FIRST!
                main_panel = await page.query_selector("#main")
                if main_panel:
                    incoming_msgs = await main_panel.query_selector_all("div.message-in")
                    if incoming_msgs:
                        last_msg = incoming_msgs[-1]
                        full_msg_text = (await last_msg.inner_text()).strip()

                        # Clean text lines
                        lines = [l.strip() for l in full_msg_text.split('\n') if l.strip()]
                        msg_text = lines[0] if lines else ""

                        # Filter out timestamps or system notifications
                        if msg_text and not msg_text.endswith("am") and not msg_text.endswith("pm") and len(msg_text) > 1:
                            msg_id = f"main_{msg_text}_{len(incoming_msgs)}"

                            if msg_id not in processed_msg_ids:
                                processed_msg_ids.add(msg_id)
                                print(f"[{now_str}] 📩 [INCOMING WHATSAPP MESSAGE DETECTED]: '{msg_text}'", flush=True)

                                # Call local backend API directly from Python
                                async with httpx.AsyncClient(timeout=15.0) as client:
                                    resp = await client.post(
                                        "http://localhost:8000/api/v1/webhooks/whatsapp/json",
                                        json={"message": msg_text, "phone": "+919823012345"}
                                    )
                                    if resp.status_code == 200:
                                        res_data = resp.json()
                                        reply_body = res_data.get("reply_body", "उत्तर प्रक्रियेत आहे.")

                                        print(f"[{now_str}] 🤖 [GENERATED GROUNDED ANSWER]:\n{reply_body[:120]}...\n", flush=True)

                                        # Target input box in footer
                                        input_box = await page.query_selector("#main footer div[contenteditable='true']")
                                        if not input_box:
                                            input_box = await page.query_selector("footer div[contenteditable='true']")
                                        if not input_box:
                                            input_box = await page.query_selector("footer p.selectable-text")

                                        if input_box:
                                            await input_box.focus()
                                            await asyncio.sleep(0.3)

                                            # Native React Lexical keyboard text insertion
                                            await page.keyboard.insert_text(reply_body)
                                            await asyncio.sleep(0.5)

                                            # Click Send button or hit Enter
                                            send_btn = await page.query_selector("button[aria-label='Send'], span[data-icon='send']")
                                            if send_btn:
                                                await send_btn.click()
                                            else:
                                                await page.keyboard.press("Enter")

                                            print(f"[{now_str}] 🚀 [SUCCESS]: REPLIED LIVE ON WHATSAPP CHAT!\n", flush=True)

                # 2. CHECK SIDEBAR CHAT ROWS (Supports Light Mode & Dark Mode virtualized lists)
                chat_rows = await page.query_selector_all("#pane-side div[role='row'], #pane-side div[role='gridcell'], div._ak8l, div._ak8i")
                for chat in chat_rows[:3]:
                    try:
                        # Only click if not already focused
                        await chat.click()
                        await asyncio.sleep(0.6)
                    except Exception:
                        pass

                await asyncio.sleep(1.2)
            except Exception as loop_err:
                await asyncio.sleep(1.2)

if __name__ == "__main__":
    asyncio.run(start_whatsapp_bot())

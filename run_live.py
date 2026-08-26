"""
All-in-one runner to start FastAPI, start Cloudflare Tunnel, and sync Vapi Voice Assistant.
Usage:
    python run_live.py
"""

import os
import sys
import time
import re
import subprocess
import requests
from dotenv import load_dotenv

load_dotenv()

from app.voice.vapi_client import VapiClient

def get_cloudflared_url(proc):
    """Parse cloudflared stderr output to find the *.trycloudflare.com URL."""
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    while True:
        line = proc.stderr.readline()
        if not line:
            break
        line_str = line.decode("utf-8", errors="ignore")
        match = url_pattern.search(line_str)
        if match:
            return match.group(0)
    return None

def main():
    print("=" * 60)
    print("🏥 Starting CareCloud Voice AI Live System...")
    print("=" * 60)

    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        print("❌ Error: VAPI_API_KEY is not set in .env")
        sys.exit(1)

    # 1. Start FastAPI backend
    print("\n🚀 [1/3] Starting FastAPI server on http://localhost:8000...")
    fastapi_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(2)

    # Verify FastAPI is responding
    try:
        r = requests.get("http://127.0.0.1:8000/health", timeout=3)
        if r.status_code == 200:
            print("✅ FastAPI backend is healthy.")
    except Exception as e:
        print(f"⚠️ Could not reach FastAPI health endpoint: {e}")

    # 2. Check for cloudflared
    print("\n🌐 [2/3] Starting Cloudflare HTTPS Tunnel for Webhook...")
    cloudflared_path = None
    if os.path.exists("./cloudflared"):
        cloudflared_path = "./cloudflared"
    else:
        cloudflared_path = subprocess.run(["which", "cloudflared"], capture_output=True, text=True).stdout.strip()
    
    tunnel_proc = None
    public_url = None

    if cloudflared_path:
        tunnel_proc = subprocess.Popen(
            [cloudflared_path, "tunnel", "--url", "http://localhost:8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("⏳ Waiting for Cloudflare tunnel URL...")
        public_url = get_cloudflared_url(tunnel_proc)
    
    if not public_url:
        # Fallback to manual prompt
        print("⚠️ Could not auto-generate Cloudflare tunnel.")
        public_url = input("Enter your public URL (e.g. from ngrok / cloudflared): ").strip()

    print(f"✅ Public Tunnel URL: {public_url}")

    # 3. Configure Vapi Assistant
    print("\n🤖 [3/3] Syncing Vapi Voice Assistant (Maya)...")
    client = VapiClient(api_key=api_key)
    assistant = client.create_or_update_assistant(server_url=public_url)
    assistant_id = assistant.get("id")
    print(f"✅ Vapi Assistant Created/Updated! (ID: {assistant_id})")

    # Link Phone Number
    phones = client.list_phone_numbers()
    phone_number_str = None
    if phones:
        phone = phones[0]
        phone_id = phone.get("id")
        phone_number_str = phone.get("number")
        client.assign_assistant_to_phone(phone_id, assistant_id)
        print(f"📞 Attached Phone Number: {phone_number_str} to Assistant Maya!")

    print("\n" + "=" * 60)
    print("🎉 CARECLOUD VOICE AI SYSTEM IS LIVE AND READY!")
    print("=" * 60)
    if phone_number_str:
        print(f"📱 DIALABLE US PHONE NUMBER: {phone_number_str}")
    print(f"💻 DASHBOARD & VOICE TESTER : {public_url}/")
    print(f"📖 SWAGGER API DOCS         : {public_url}/docs")
    print("=" * 60)
    print("Press Ctrl+C to stop.\n")

    try:
        fastapi_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        fastapi_proc.terminate()
        if tunnel_proc:
            tunnel_proc.terminate()
        print("Done.")

if __name__ == "__main__":
    main()

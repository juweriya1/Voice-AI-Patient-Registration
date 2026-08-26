"""
Setup script to automatically create/update Vapi Assistant and link phone numbers.
Usage:
    python scripts/setup_vapi_agent.py --server-url https://your-domain.ngrok-free.app
"""

import os
import sys
import argparse
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from app.voice.vapi_client import VapiClient

def main():
    parser = argparse.ArgumentParser(description="Configure Vapi Voice AI Agent")
    parser.add_argument("--server-url", type=str, help="Public URL of this server (e.g., https://xyz.ngrok-free.app)")
    parser.add_argument("--assistant-id", type=str, help="Existing Vapi Assistant ID to update")
    parser.add_argument("--buy-phone", action="store_true", help="Automatically buy a US phone number if none exist")
    args = parser.parse_args()

    api_key = os.getenv("VAPI_API_KEY")
    if not api_key:
        print("❌ Error: VAPI_API_KEY is not set in environment or .env file.")
        print("Please set VAPI_API_KEY in your .env file.")
        sys.exit(1)

    server_url = args.server_url or os.getenv("BASE_URL")
    if not server_url or "localhost" in server_url:
        print("⚠️ Warning: server_url is pointing to localhost. Telephony webhooks require a publicly accessible URL (ngrok/Railway/Render).")
        server_url = input("Enter public server URL (e.g. https://...ngrok-free.app): ").strip()

    client = VapiClient(api_key=api_key)
    assistant_id = args.assistant_id or os.getenv("VAPI_ASSISTANT_ID")

    print(f"🚀 Configuring Vapi Assistant with server webhook: {server_url}...")
    try:
        assistant = client.create_or_update_assistant(server_url=server_url, assistant_id=assistant_id)
        asst_id = assistant.get("id")
        print(f"✅ Vapi Assistant Ready! ID: {asst_id}")
        print(f"   Name: {assistant.get('name')}")
        print(f"   Voice: {assistant.get('voice', {}).get('voiceId')}")

        # Check Phone Numbers
        print("🔍 Checking provisioned phone numbers in Vapi...")
        phones = client.list_phone_numbers()
        if phones:
            for p in phones:
                phone_id = p.get("id")
                number = p.get("number")
                print(f"📞 Found Phone Number: {number} (ID: {phone_id})")
                client.assign_assistant_to_phone(phone_id, asst_id)
                print(f"🔗 Linked phone number {number} to Assistant {asst_id}!")
                print(f"\n🎉 ALL SET! You can now dial {number} to test patient registration!")
        else:
            print("ℹ️ No phone numbers found in Vapi account.")
            if args.buy_phone:
                print("🛒 Purchasing a US phone number via Vapi...")
                new_phone = client.buy_phone_number()
                phone_id = new_phone.get("id")
                number = new_phone.get("number")
                print(f"✅ Bought Phone Number: {number}")
                client.assign_assistant_to_phone(phone_id, asst_id)
                print(f"🎉 Linked and ready to dial: {number}")
            else:
                print("👉 Go to https://dashboard.vapi.ai/phone-numbers to buy or import a phone number, or run with --buy-phone")

    except Exception as e:
        print(f"❌ Error setting up Vapi agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

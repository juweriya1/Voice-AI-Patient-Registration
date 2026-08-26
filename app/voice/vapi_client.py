"""
Vapi REST API Client for automated assistant and phone number management.
"""

import os
import requests
from typing import Optional, Dict, Any, List
from app.voice.prompts import SYSTEM_PROMPT
from app.voice.tools import VAPI_TOOLS

VAPI_BASE_URL = "https://api.vapi.ai"

class VapiClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VAPI_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 5)

    def create_or_update_assistant(self, server_url: str, assistant_id: Optional[str] = None) -> Dict[str, Any]:
        """Create or update a Vapi Voice AI Assistant with patient registration tools."""
        if not self.is_configured():
            raise ValueError("VAPI_API_KEY is not set.")

        payload = {
            "name": "CareCloud Patient Intake Agent",
            "model": {
                "provider": "openai",
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    }
                ],
                "tools": VAPI_TOOLS,
                "temperature": 0.2
            },
            "voice": {
                "provider": "11labs",
                "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel - warm, natural healthcare tone
                "speed": 1.0
            },
            "firstMessage": "Hello! Thank you for calling CareCloud Patient Registration. My name is Maya. I'd be happy to help get you registered today. Could I start with your first and last name?",
            "firstMessageMode": "assistant-speaks-first",
            "serverUrl": f"{server_url.rstrip('/')}/api/voice/vapi/webhook",
            "serverUrlSecret": os.getenv("VAPI_WEBHOOK_SECRET", ""),
            "endCallMessage": "Thank you for choosing CareCloud. Have a wonderful day!",
            "recordingEnabled": True,
            "silenceTimeoutSeconds": 30,
            "maxDurationSeconds": 600
        }

        if assistant_id:
            url = f"{VAPI_BASE_URL}/assistant/{assistant_id}"
            resp = requests.patch(url, json=payload, headers=self.headers)
        else:
            url = f"{VAPI_BASE_URL}/assistant"
            resp = requests.post(url, json=payload, headers=self.headers)

        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to create/update Vapi assistant: {resp.status_code} - {resp.text}")

        return resp.json()

    def list_phone_numbers(self) -> List[Dict[str, Any]]:
        """List phone numbers provisioned in Vapi account."""
        if not self.is_configured():
            return []
        url = f"{VAPI_BASE_URL}/phone-number"
        resp = requests.get(url, headers=self.headers)
        if resp.status_code == 200:
            return resp.json()
        return []

    def assign_assistant_to_phone(self, phone_number_id: str, assistant_id: str) -> Dict[str, Any]:
        """Assign an assistant to a phone number in Vapi."""
        if not self.is_configured():
            raise ValueError("VAPI_API_KEY is not set.")
        url = f"{VAPI_BASE_URL}/phone-number/{phone_number_id}"
        payload = {"assistantId": assistant_id}
        resp = requests.patch(url, json=payload, headers=self.headers)
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to link phone to assistant: {resp.status_code} - {resp.text}")
        return resp.json()

    def buy_phone_number(self, area_code: Optional[str] = "415") -> Dict[str, Any]:
        """Buy a US phone number via Vapi."""
        if not self.is_configured():
            raise ValueError("VAPI_API_KEY is not set.")
        url = f"{VAPI_BASE_URL}/phone-number/buy"
        payload = {"areaCode": area_code} if area_code else {}
        resp = requests.post(url, json=payload, headers=self.headers)
        if resp.status_code not in (200, 201):
            raise Exception(f"Failed to buy phone number: {resp.status_code} - {resp.text}")
        return resp.json()

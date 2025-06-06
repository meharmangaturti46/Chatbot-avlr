from fastapi import FastAPI, Request
from botbuilder.core import BotFrameworkAdapter, TurnContext
from botbuilder.schema import Activity
import os
import requests

app = FastAPI()
adapter = BotFrameworkAdapter(
    app_id=os.getenv("MICROSOFT_APP_ID", ""),
    app_password=os.getenv("MICROSOFT_APP_PASSWORD", "")
)

BACKEND_CHAT_URL = os.getenv("BACKEND_CHAT_URL", "http://localhost:8000/api/chat/")

@app.post("/api/teams/messages")
async def messages(request: Request):
    body = await request.json()
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")

    async def aux_func(turn_context: TurnContext):
        user_id = activity.from_property.id
        user_message = activity.text
        resp = requests.post(BACKEND_CHAT_URL, json={
            "message": user_message,
            "channel": "teams"
        }, headers={"Authorization": f"Bearer {os.getenv('BOT_BACKEND_JWT', '')}"})
        ai_response = resp.json().get("response", "Sorry, no response.")
        reply = Activity(type="message", text=ai_response)
        await turn_context.send_activity(reply)

    await adapter.process_activity(activity, auth_header, aux_func)
    return ""
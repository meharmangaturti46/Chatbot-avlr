import os
import logging
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import dialogflow_v2 as dialogflow
import requests
from jose import jwt, JWTError
from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/hrms")
DIALOGFLOW_PROJECT_ID = os.getenv("DIALOGFLOW_PROJECT_ID", "dialogflow-project-id")
RASA_URL = os.getenv("RASA_URL", "http://localhost:5005/model/parse")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = "HS256"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Secure this in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

session_client = dialogflow.SessionsClient()

def verify_jwt(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication")

def query_dialogflow(session_id, text):
    session = session_client.session_path(DIALOGFLOW_PROJECT_ID, session_id)
    text_input = dialogflow.types.TextInput(text=text, language_code="en")
    query_input = dialogflow.types.QueryInput(text=text_input)
    response = session_client.detect_intent(session=session, query_input=query_input)
    return {
        "text": response.query_result.fulfillment_text,
        "intent": response.query_result.intent.display_name,
        "confidence": response.query_result.intent_detection_confidence,
        "is_fallback": response.query_result.intent.is_fallback
    }

def query_rasa(text, session_id):
    resp = requests.post(RASA_URL, json={"text": text, "sender": session_id})
    resp.raise_for_status()
    data = resp.json()
    return data.get("text", "Sorry, I could not understand that.")

def log_chat(user_id, message, response, channel):
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO chat_logs (user_id, message, response, channel) VALUES (:uid, :msg, :resp, :ch)"),
            {"uid": user_id, "msg": message, "resp": response, "ch": channel}
        )

def send_notification(user_id, event_type, details):
    logger.info(f"Notify {user_id}: {event_type} - {details}")

@app.post("/api/chat/")
async def chat(
    request: Request,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(verify_jwt)
):
    data = await request.json()
    user_id = token_data["sub"]
    message = data.get("message")
    channel = data.get("channel", "web")
    if not message:
        raise HTTPException(status_code=400, detail="Message required")

    df_result = query_dialogflow(str(user_id), message)
    if df_result["is_fallback"]:
        ai_response = query_rasa(message, user_id)
    else:
        ai_response = df_result["text"]

    background_tasks.add_task(log_chat, user_id, message, ai_response, channel)
    return {"response": ai_response, "intent": df_result["intent"]}

@app.get("/api/history")
def chat_history(
    limit: int = Query(100, ge=1, le=500),
    token_data: dict = Depends(verify_jwt)
):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT message, response, channel, created_at FROM chat_logs WHERE user_id=:uid ORDER BY created_at DESC LIMIT :lim"),
            {"uid": user_id, "lim": limit}
        )
        return [dict(row) for row in result]

@app.get("/api/analytics")
def chat_analytics(token_data: dict = Depends(verify_jwt)):
    with engine.connect() as conn:
        total_sessions = conn.execute(text("SELECT COUNT(DISTINCT user_id) FROM chat_logs")).scalar()
        total_messages = conn.execute(text("SELECT COUNT(*) FROM chat_logs")).scalar()
        top_intents = conn.execute(text("SELECT response, COUNT(*) as count FROM chat_logs GROUP BY response ORDER BY count DESC LIMIT 5"))
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "top_responses": [dict(row) for row in top_intents]
        }

@app.post("/api/leave/apply")
def leave_apply(
    start_date: str,
    end_date: str,
    leave_type: str,
    reason: Optional[str] = None,
    token_data: dict = Depends(verify_jwt)
):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO leave_requests (user_id, start_date, end_date, type, reason, status) VALUES (:uid, :sd, :ed, :lt, :rs, 'pending')"),
            {"uid": user_id, "sd": start_date, "ed": end_date, "lt": leave_type, "rs": reason}
        )
    send_notification(user_id, "LeaveApplied", f"{leave_type} from {start_date} to {end_date}")
    return {"status": "Leave request submitted"}

@app.get("/api/leave/status")
def leave_status(token_data: dict = Depends(verify_jwt)):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, start_date, end_date, type, status, reason, created_at FROM leave_requests WHERE user_id=:uid ORDER BY created_at DESC LIMIT 5"),
            {"uid": user_id}
        )
        return [dict(row) for row in result]

@app.get("/api/leave/balance")
def leave_balance(token_data: dict = Depends(verify_jwt)):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT leave_type, balance FROM leave_balances WHERE user_id=:uid"),
            {"uid": user_id}
        )
        return [dict(row) for row in result]

@app.get("/api/attendance/today")
def attendance_today(token_data: dict = Depends(verify_jwt)):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT punch_in, punch_out, status FROM attendance WHERE user_id=:uid AND date=current_date"),
            {"uid": user_id}
        )
        row = result.fetchone()
        return dict(row) if row else {"status": "No attendance record found."}

@app.get("/api/attendance/history")
def attendance_history(
    days: int = Query(7, ge=1, le=31),
    token_data: dict = Depends(verify_jwt)
):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT date, punch_in, punch_out, status FROM attendance WHERE user_id=:uid ORDER BY date DESC LIMIT :days"),
            {"uid": user_id, "days": days}
        )
        return [dict(row) for row in result]

@app.get("/api/payslip/latest")
def payslip_latest(token_data: dict = Depends(verify_jwt)):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT url, date FROM payslips WHERE user_id=:uid ORDER BY date DESC LIMIT 1"),
            {"uid": user_id}
        )
        row = result.fetchone()
        return dict(row) if row else {"payslip_url": None}

@app.get("/api/payslip/history")
def payslip_history(
    months: int = Query(6, ge=1, le=24),
    token_data: dict = Depends(verify_jwt)
):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT url, date FROM payslips WHERE user_id=:uid ORDER BY date DESC LIMIT :months"),
            {"uid": user_id, "months": months}
        )
        return [dict(row) for row in result]

@app.get("/api/tax/summary")
def tax_summary(token_data: dict = Depends(verify_jwt)):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT year, total_income, tax_paid, tax_due FROM tax_summary WHERE user_id=:uid ORDER BY year DESC LIMIT 3"),
            {"uid": user_id}
        )
        return [dict(row) for row in result]

@app.get("/api/onboarding/status")
def onboarding_status(token_data: dict = Depends(verify_jwt)):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT step, completed, notes FROM onboarding_steps WHERE user_id=:uid ORDER BY step"),
            {"uid": user_id}
        )
        return [dict(row) for row in result]

@app.get("/api/onboarding/documents")
def onboarding_documents(token_data: dict = Depends(verify_jwt)):
    user_id = token_data["sub"]
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT document, status, url FROM onboarding_documents WHERE user_id=:uid"),
            {"uid": user_id}
        )
        return [dict(row) for row in result]

@app.get("/api/policy/{policy_name}")
def hr_policy(policy_name: str, token_data: dict = Depends(verify_jwt)):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name, content FROM hr_policies WHERE LOWER(name)=LOWER(:pn)"),
            {"pn": policy_name}
        )
        row = result.fetchone()
        return dict(row) if row else {"content": "Policy not found."}

@app.get("/api/faq")
def faqs(token_data: dict = Depends(verify_jwt)):
    with engine.connect() as conn:
        result = conn.execute(text("SELECT question, answer FROM hr_faqs ORDER BY id"))
        return [dict(row) for row in result]

@app.get("/api/reimbursement/process")
def reimbursement_process(token_data: dict = Depends(verify_jwt)):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT process, notes FROM reimbursement_process ORDER BY step")
        )
        return [dict(row) for row in result]

@app.get("/api/holiday/calendar")
def holiday_calendar(
    year: Optional[int] = None,
    token_data: dict = Depends(verify_jwt)
):
    with engine.connect() as conn:
        query = "SELECT date, name FROM holiday_calendar"
        params = {}
        if year:
            query += " WHERE EXTRACT(YEAR FROM date) = :year"
            params["year"] = year
        query += " ORDER BY date"
        result = conn.execute(text(query), params)
        return [dict(row) for row in result]

@app.post("/api/hrms/webhook")
async def hrms_webhook(request: Request):
    data = await request.json()
    user_id = data.get("user_id")
    event_type = data.get("event_type")
    details = data.get("details")
    send_notification(user_id, event_type, details)
    return {"status": "notified"}

@app.get("/api/healthz")
def health_check():
    return {"status": "ok"}
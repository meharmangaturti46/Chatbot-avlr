# HRMS AI Chatbot Solution

This repository contains an advanced HRMS AI Chatbot stack:
- **Backend:** FastAPI + PostgreSQL + Dialogflow/Rasa integration
- **Frontend:** React
- **NLP:** Rasa NLU or Dialogflow (configurable)
- **Integrations:** Web, Microsoft Teams
- **Deployment:** Designed for AWS, Docker, or local

## Structure

- `backend/`: Python FastAPI backend, DB schema, Teams adapter, requirements
- `rasa/`: Rasa NLU files, actions, sample stories and domain
- `frontend/`: React single-page app

## Quick Start

1. Install backend dependencies:
    ```sh
    cd backend
    pip install -r requirements.txt
    ```
2. Set up PostgreSQL using `schema.sql`.
3. Configure environment variables in `.env`.
4. Start backend:
    ```sh
    uvicorn main:app --reload
    ```
5. Install and start frontend:
    ```sh
    cd ../frontend
    npm install
    npm start
    ```
6. (Optional) Set up Rasa:
    ```sh
    cd ../rasa
    pip install rasa-sdk
    rasa train
    rasa run actions
    rasa shell
    ```

## Download

[Download ZIP](https://github.com/<your-username>/hrms-chatbot/archive/refs/heads/main.zip)
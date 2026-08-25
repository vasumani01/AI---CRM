from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import initialize_database
from schemas import ChatRequest
from tools import get_all_deals, get_all_customers
from agent import chat_with_crm


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="AI-Powered CRM Assistant",
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "AI CRM Assistant API is running."
    }


@app.get("/api/customers")
def customers():
    return {
        "customers": get_all_customers()
    }


@app.get("/api/deals")
def deals():
    return {
        "deals": get_all_deals()
    }


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        return chat_with_crm(request.message)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
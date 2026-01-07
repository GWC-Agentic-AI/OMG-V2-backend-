
from contextlib import asynccontextmanager
from fastapi import Request
from fastapi.responses import JSONResponse
from utils.logger import get_logger

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chatbot.chat import router as chat_router
from api.chatbot.history import router as history_router
from api.quiz.generate import router as generate_quiz_router
from api.quiz.translate import router as translate_auiz_router

logger = get_logger('Server')

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application")
    try:
        yield
    finally:
        logger.info("Shutting down application")


app = FastAPI(lifespan=lifespan, title="OMG ChatBot", version="1.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/bot")
app.include_router(history_router, prefix="/bot")
app.include_router(generate_quiz_router,prefix="/quiz", tags=["Quiz"])
app.include_router(translate_auiz_router,prefix="/quiz", tags=["Quiz"])


@app.get("/")
def main():
    return {"status": 200, "details": "OMG ChatBot is running"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

# UNCOMMAND FOR LOCAL MACHINE TESTING
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)


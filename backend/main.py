from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from apis.connect_gmail import router as gmail_router
from apis.auth import router as auth_router
from apis.inbox import router as inbox_router
from apis.settings import router as settings_router
from apis.prompt_settings import router as prompt_settings_router
from services.email_polling_service import email_polling_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background task for email polling
polling_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global polling_task
    logger.info("🚀 Starting email polling service...")
    polling_task = asyncio.create_task(email_polling_service.start_polling_all_users())
    yield
    # Shutdown
    logger.info("🛑 Stopping email polling service...")
    email_polling_service.stop()
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

# Create FastAPI app instance with lifespan events
app = FastAPI(title="Finance Inbox API", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth_router)   # Authentication routes (/auth/*)
app.include_router(inbox_router)  # Inbox routes (/inbox/*)
app.include_router(gmail_router)  # Gmail OAuth routes (/google-auth/*)
app.include_router(settings_router)  # Settings routes (/settings/*)
app.include_router(prompt_settings_router)  # Prompt settings routes (/settings/prompt/*)

@app.get("/")
async def root():
    return {"message": "Finance Inbox API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

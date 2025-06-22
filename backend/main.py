from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apis.connect_gmail import router as gmail_router
from apis.auth import router as auth_router
from apis.inbox import router as inbox_router
from apis.debug import router as debug_router

# Create FastAPI app instance
app = FastAPI(title="Finance Inbox API", version="1.0.0")

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
app.include_router(debug_router)  # Debug routes (/debug/*) - Remove in production

@app.get("/")
async def root():
    return {"message": "Finance Inbox API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

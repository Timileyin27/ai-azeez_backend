from fastapi import FastAPI
from app.database import engine,Base
from app.routers import user,login,conversation,ws
Base.metadata.create_all(bind=engine)
from fastapi.middleware.cors import CORSMiddleware
app= FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081","https://ai-azeez.vercel.app"
                   "https://smart-convo-ui.lovable.app",
        "https://id-preview--f3e156f9-29b9-4a45-871a-e42c215b14d1.lovable.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    

)
app.include_router(user.router)
app.include_router(login.router)
app.include_router(conversation.router)
app.include_router(ws.router)


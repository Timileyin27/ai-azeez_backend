from fastapi import FastAPI
from app.database import engine,Base
from app.routers import user,login
Base.metadata.create_all(bind=engine)
from fastapi.middleware.cors import CORSMiddleware
app= FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8081","https://ai-azeez.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(user.router)
app.include_router(login.router)


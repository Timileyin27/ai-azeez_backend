from fastapi import FastAPI
from app.database import engine,Base
from app.routers import user,login
Base.metadata.create_all(bind=engine)
app= FastAPI()

app.include_router(user.router)
app.include_router(login.router)


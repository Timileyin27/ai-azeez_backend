from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
import app.models
import app.models.users
import app.schemas.chat as schemas
import app.models.chat as models
import app.oauth2   
router = APIRouter(prefix="/conversation", tags=["Conversation"])
@router.post("/", status_code=status.HTTP_201_CREATED)
def create_conversation(payload: schemas.conversationIN, db: Session = Depends(get_db), current_user: app.models.users.User = Depends(app.oauth2.get_current_user)):
    new_conversation = models.Conversation(
        title=payload.title,
        user_id=current_user.id
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation
@router.get("/", response_model=list[schemas.conversationOUT])
def get_conversations(db: Session = Depends(get_db), current_user: app.models.users.User = Depends(app.oauth2.get_current_user)):
    conversations = db.query(models.Conversation).filter(models.Conversation.user_id == current_user.id).all()
    return conversations
@router.get("/{conversation_id}", response_model=schemas.conversationOUT)
def get_conversation(conversation_id: str, db: Session = Depends(get_db), current_user: app.models.users.User = Depends(app.oauth2.get_current_user)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id, models.Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conversation
@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db), current_user: app.models.users.User = Depends(app.oauth2.get_current_user)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id, models.Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"detail": "Conversation deleted"}
@router.put("/{conversation_id}", response_model=schemas.conversationOUT)
def update_conversation(conversation_id: str, payload: schemas.conversationIN, db: Session = Depends(get_db), current_user: app.models.users.User = Depends(app.oauth2.get_current_user)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id, models.Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    conversation.title = payload.title
    db.commit()
    db.refresh(conversation)
    return conversation
@router.post("/{conversation_id}/message",status_code=status.HTTP_201_CREATED)
def create_chat(conversation_id: str,payload: schemas.messageIN,db: Session=Depends(get_db),current_user: app.models.users.User = Depends(app.oauth2.get_current_user)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id, models.Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    new_message=models.Message(conversation_id=conversation.id,role="user",content=payload.content)
    db.add(new_message)
    db.commit()
    db.refresh(new_message)
    return new_message
@router.get("/{conversation_id}/message",response_model=list[schemas.messageOUT])
def getMessage(conversation_id: str,db: Session=Depends(get_db),current_user: app.models.users.User = Depends(app.oauth2.get_current_user)):
    conversation = db.query(models.Conversation).filter(models.Conversation.id == conversation_id, models.Conversation.user_id == current_user.id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    message=db.query(models.Message).filter(models.Message.conversation_id==conversation_id).all()
    return message
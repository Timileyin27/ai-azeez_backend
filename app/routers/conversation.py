from app.database import get_db
from fastapi import APIRouter, Depends, HTTPException, status,Query
from sqlalchemy.orm import Session
from sqlalchemy import func
import app.models
import uuid
import app.models.users
import app.schemas.chat as schemas
import app.models.chat as models
import app.oauth2   
router = APIRouter(prefix="/conversation", tags=["Conversation"])
def get_owned_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: app.models.users.User = Depends(app.oauth2.get_current_user),
) -> models.Conversation:
    conversation = (
        db.query(models.Conversation)
        .filter(
            models.Conversation.id == conversation_id,
            models.Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        # Same 404 whether it doesn't exist or belongs to someone else.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    return conversation
 
 
@router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=schemas.conversationOUT
)
def create_conversation(
    payload: schemas.conversationIN,
    db: Session = Depends(get_db),
    current_user: app.models.users.User = Depends(app.oauth2.get_current_user),
):
    new_conversation = models.Conversation(
        title=payload.title, user_id=current_user.id
    )
    db.add(new_conversation)
    db.commit()
    db.refresh(new_conversation)
    return new_conversation
 
 
@router.get("/", response_model=list[schemas.conversationOUT])
def get_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: app.models.users.User = Depends(app.oauth2.get_current_user),
):
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == current_user.id)
        .order_by(models.Conversation.updated_at.desc())  # most recent activity first
        .limit(limit)
        .offset(offset)
        .all()
    )
 
 
@router.get("/{conversation_id}", response_model=schemas.conversationOUT)
def get_conversation(
    conversation: models.Conversation = Depends(get_owned_conversation),
):
    return conversation
 
 
@router.put("/{conversation_id}", response_model=schemas.conversationOUT)
def update_conversation(
    payload: schemas.conversationIN,
    conversation: models.Conversation = Depends(get_owned_conversation),
    db: Session = Depends(get_db),
):
    conversation.title = payload.title
    db.commit()
    db.refresh(conversation)
    return conversation
 
 
@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation: models.Conversation = Depends(get_owned_conversation),
    db: Session = Depends(get_db),
):
    db.delete(conversation)
    db.commit()
    # 204 means "no content": return nothing.
 
 
@router.post(
    "/{conversation_id}/message",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.messageOUT,
)
def create_chat(
    payload: schemas.messageIN,
    conversation: models.Conversation = Depends(get_owned_conversation),
    db: Session = Depends(get_db),
):
    new_message = models.Message(
        conversation_id=conversation.id,
        role=models.MessageRole.user,
        content=payload.content,
    )
    db.add(new_message)
    conversation.updated_at = func.now()  # keeps the chat list sorted by activity
    db.commit()
    db.refresh(new_message)
    return new_message
 
 
@router.get("/{conversation_id}/message", response_model=list[schemas.messageOUT])
def get_messages(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    conversation: models.Conversation = Depends(get_owned_conversation),
    db: Session = Depends(get_db),
):
    """offset=0 returns the most recent `limit` messages; increase offset to
    load older pages. Each page is returned oldest-first, ready to display."""
    rows = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )
    return list(reversed(rows))
 
from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("No DATABASE_URL set for the application")
 
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatResponseModel(Base):
    __tablename__ = "chat_responses"
    id = Column(Integer, primary_key=True, index=True)
    trigger = Column(String(255), unique=True, index=True)
    response = Column(String(1024))
    active = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

# --- FastAPI App ---
app = FastAPI(title="Chat Bot Response Database Service")

# --- Pydantic Schemas ---
class ChatResponse(BaseModel):
    trigger: str
    response: str
    active: bool = True

    class Config:
        orm_mode = True

class ChatResponseOut(ChatResponse):
    id: int

# --- Dependency: Database Session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CRUD Endpoints ---

@app.get("/responses", response_model=List[ChatResponseOut])
def get_all_responses(db: Session = Depends(get_db)):
    """Get all chat responses."""
    responses = db.query(ChatResponseModel).all()
    return responses

@app.get("/responses/{response_id}", response_model=ChatResponseOut)
def get_response(response_id: int, db: Session = Depends(get_db)):
    """Get a specific chat response by ID."""
    resp = db.query(ChatResponseModel).filter(ChatResponseModel.id == response_id).first()
    if not resp:
        raise HTTPException(status_code=404, detail="Response not found")
    return resp

@app.post("/responses", response_model=ChatResponseOut)
def create_response(chat_response: ChatResponse, db: Session = Depends(get_db)):
    """Create a new chat response."""
    # Check if a response for the same trigger already exists.
    existing = db.query(ChatResponseModel).filter(ChatResponseModel.trigger == chat_response.trigger).first()
    if existing:
        raise HTTPException(status_code=400, detail="Response for this trigger already exists")
    db_response = ChatResponseModel(**chat_response.dict())
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response

@app.put("/responses/{response_id}", response_model=ChatResponseOut)
def update_response(response_id: int, updated_response: ChatResponse, db: Session = Depends(get_db)):
    """Update an existing chat response."""
    db_response = db.query(ChatResponseModel).filter(ChatResponseModel.id == response_id).first()
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found")
    for key, value in updated_response.dict().items():
        setattr(db_response, key, value)
    db.commit()
    db.refresh(db_response)
    return db_response

@app.delete("/responses/{response_id}", response_model=ChatResponseOut)
def delete_response(response_id: int, db: Session = Depends(get_db)):
    """Delete a chat response."""
    db_response = db.query(ChatResponseModel).filter(ChatResponseModel.id == response_id).first()
    if not db_response:
        raise HTTPException(status_code=404, detail="Response not found")
    db.delete(db_response)
    db.commit()
    return db_response

@app.get("/respond", response_model=ChatResponseOut)
def respond_to_input(input_text: str = Query(..., description="The user input to check for a trigger"), 
                     db: Session = Depends(get_db)):
    """
    Given an input text, find the corresponding active chat response.
    This endpoint can be used by your chat bot to fetch a reply.
    """
    response_entry = db.query(ChatResponseModel)\
                       .filter(ChatResponseModel.trigger.ilike(f"%{input_text.lower()}%"))\
                       .filter(ChatResponseModel.active == True)\
                       .first()
    if not response_entry:
        raise HTTPException(status_code=404, detail="No matching response found")
    return response_entry

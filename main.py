from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from agent import Agent
import os
import io
from pypdf import PdfReader
from dotenv import load_dotenv
import subprocess
import re
import uuid
from pathlib import Path
import shutil
import traceback
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import models, database, auth

load_dotenv()

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Ensure generated directory exists
GENERATED_DIR = Path("static/generated")
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

# Initialize the agent
agent = Agent()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    pdf_url: Optional[str] = None
    cv_content: Optional[str] = None

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserResponse(BaseModel):
    email: str
    full_name: str
    is_active: bool
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, db: Session = Depends(auth.get_db), current_user: models.User = Depends(auth.get_current_user)):
    # 1. Load history from DB
    db_messages = db.query(models.Message).filter(models.Message.user_id == current_user.id).order_by(models.Message.timestamp.asc()).all()
    
    
    # 3. Inject Context if available
    system_message = agent.system_prompt
    if current_user.cv_text:
        system_message += f"\n\nCURRENT USER CV:\n{current_user.cv_text}"
    if current_user.jd_text:
        system_message += f"\n\nTARGET JOB DESCRIPTION:\n{current_user.jd_text}"
        
    history = [{"role": "system", "content": system_message}]
    for msg in db_messages:
        history.append({"role": msg.role, "content": msg.content})
    
    # 4. Call Agent (stateless)
    response_text = agent.chat(request.message, history=history)
    
    # 5. Save User Message
    user_msg = models.Message(user_id=current_user.id, role="user", content=request.message)
    db.add(user_msg)
    
    # 6. Save Assistant Message
    assistant_msg = models.Message(user_id=current_user.id, role="assistant", content=response_text)
    db.add(assistant_msg)
    
    db.commit()
    
    return ChatResponse(response=response_text)

@app.post("/api/update_context")
async def update_context(
    file: Optional[UploadFile] = File(None), 
    job_description: Optional[str] = Form(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(auth.get_db)
):
    if file:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files allowed")
        
        # Save temp
        temp_filename = f"temp_{uuid.uuid4()}.pdf"
        with open(temp_filename, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Extract text
        try:
            reader = PdfReader(temp_filename)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            current_user.cv_text = text
        except Exception as e:
            os.remove(temp_filename)
            raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
    
    if job_description:
        current_user.jd_text = job_description
        
    db.commit()
    return {"status": "success", "message": "Context updated"}

@app.post("/api/tailor_cv", response_model=ChatResponse)
async def tailor_cv_endpoint(file: UploadFile = File(...), job_description: str = Form(...), current_user: models.User = Depends(auth.get_current_user)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        # Read PDF content
        content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        cv_text = ""
        for page in pdf_reader.pages:
            cv_text += page.extract_text() + "\n"
            
        # Call agent to tailor CV
        response_text = agent.tailor_cv(cv_text, job_description)
        latex_code = None
        
        # Extract CV Content (Markdown/Text)
        # Try parsing using new delimiters
        if "[CV_START]" in response_text:
            print("CV Delimiter [CV_START] found!")
            parts = response_text.split("[CV_START]")
            response_text = parts[0].strip() # Analysis part
            
            # content after start tag
            remaining = parts[1]
            if "[CV_END]" in remaining:
                cv_content = remaining.split("[CV_END]")[0].strip()
            else:
                print("Warning: [CV_END] missing, taking rest of string.")
                cv_content = remaining.strip()
        else:
             print("No CV content delimiter found. Treating full response as analysis.")
             cv_content = None

        return ChatResponse(response=response_text, cv_content=cv_content)
    except Exception as e:
        traceback.print_exc() # Print full traceback
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/reset")
async def reset_history(current_user: models.User = Depends(auth.get_current_user)):
    agent.clear_history()
    return {"status": "History cleared"}

@app.post("/api/analyze_jd", response_model=ChatResponse)
async def analyze_jd_endpoint(file: UploadFile = File(...), job_description: str = Form(...), current_user: models.User = Depends(auth.get_current_user)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        cv_text = ""
        for page in pdf_reader.pages:
            cv_text += page.extract_text() + "\n"
        response = agent.analyze_jd(job_description, cv_text)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/extract_skills", response_model=ChatResponse)
async def extract_skills_endpoint(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        cv_text = ""
        for page in pdf_reader.pages:
            cv_text += page.extract_text() + "\n"
        response = agent.extract_skills(cv_text)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/ats_score", response_model=ChatResponse)
async def ats_score_endpoint(file: UploadFile = File(...), current_user: models.User = Depends(auth.get_current_user)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        content = await file.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        cv_text = ""
        for page in pdf_reader.pages:
            cv_text += page.extract_text() + "\n"
        response = agent.estimate_ats_score(cv_text)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

class SummarizeRequest(BaseModel):
    job_description: str

@app.post("/api/summarize_jd", response_model=ChatResponse)
async def summarize_jd_endpoint(request: SummarizeRequest, current_user: models.User = Depends(auth.get_current_user)):
    response = agent.summarize_jd(request.job_description)
    return ChatResponse(response=response)

# Mount static files
@app.post("/api/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(auth.get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, full_name=user.full_name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(auth.get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/users/me", response_model=UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user

# Mount static files
# Mount generated files explicitly
app.mount("/generated", StaticFiles(directory="static/generated"), name="generated")

# Mount static files (root fallback)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

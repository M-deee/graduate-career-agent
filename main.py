from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent import Agent
import os
import io
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Initialize the agent
agent = Agent()

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str



@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    response = agent.chat(request.message)
    return ChatResponse(response=response)

@app.post("/api/tailor_cv", response_model=ChatResponse)
async def tailor_cv_endpoint(file: UploadFile = File(...), job_description: str = Form(...)):
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
        response = agent.tailor_cv(cv_text, job_description)
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/reset")
async def reset_history():
    agent.clear_history()
    return {"status": "History cleared"}

@app.post("/api/analyze_jd", response_model=ChatResponse)
async def analyze_jd_endpoint(file: UploadFile = File(...), job_description: str = Form(...)):
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
async def extract_skills_endpoint(file: UploadFile = File(...)):
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
async def ats_score_endpoint(file: UploadFile = File(...)):
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
async def summarize_jd_endpoint(request: SummarizeRequest):
    response = agent.summarize_jd(request.job_description)
    return ChatResponse(response=response)

# Mount static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

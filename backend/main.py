from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from agent import run_analysis

app = FastAPI(title="ClaimGuard AI API")

# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DocumentPayload(BaseModel):
    text: str

@app.post("/api/analyze")
async def analyze_document(payload: DocumentPayload):
    if not payload.text:
        raise HTTPException(status_code=400, detail="Document text is required.")
    
    try:
        # Invoke the LangGraph workflow
        analysis_result = run_analysis(payload.text)
        
        return {
            "status": "success",
            "data": {
                "extracted": analysis_result.get("extracted_data"),
                "summary": analysis_result.get("translated_summary"),
                "questions": analysis_result.get("suggested_questions")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
import json

# Define the State for our LangGraph
class BillState(TypedDict):
    document_text: str
    extracted_data: dict
    translated_summary: str
    suggested_questions: list[str]

# Initialize the Gemini model 
llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite", temperature=0)

def parse_ai_text(content) -> str:
    """Helper function to safely extract text whether Gemini returns a string or a list."""
    if isinstance(content, list):
        return content[0].get("text", str(content[0])) if isinstance(content[0], dict) else str(content[0])
    return str(content)

def extract_entities(state: BillState):
    """Simulates RAG and entity extraction to find charges and codes."""
    prompt = f"Extract total charges, out-of-network fees, and CPT codes from this bill:\n{state['document_text']}\nReturn ONLY valid JSON with keys: total_charges, unexpected_fees, cpt_codes."
    response = llm.invoke([HumanMessage(content=prompt)])
    
    text_content = parse_ai_text(response.content)
        
    try:
        clean_text = text_content.replace('```json', '').replace('```', '').strip()
        extracted = json.loads(clean_text)
    except Exception:
        extracted = {"error": "Failed to parse document entities."}
        
    return {"extracted_data": extracted}

def translate_terminology(state: BillState):
    """Translates complex extracted terms into plain English."""
    data = state.get("extracted_data", {})
    prompt = f"Explain these billing entities in simple 8th-grade English: {data}"
    response = llm.invoke([HumanMessage(content=prompt)])
    
    text_content = parse_ai_text(response.content)
    
    return {"translated_summary": text_content}

def generate_questions(state: BillState):
    """Generates personalized questions for the healthcare provider."""
    data = state.get("extracted_data", {})
    prompt = f"Based on these charges: {data}, suggest 3 polite questions the patient should ask their provider to clarify the bill."
    response = llm.invoke([HumanMessage(content=prompt)])
    
    text_content = parse_ai_text(response.content)
    
    # Safely split the cleaned text into a list of strings
    questions = text_content.split('\n')
    
    return {"suggested_questions": [q.strip() for q in questions if q.strip()]}

# Build the LangGraph
workflow = StateGraph(BillState)

# Add nodes
workflow.add_node("extract", extract_entities)
workflow.add_node("translate", translate_terminology)
workflow.add_node("generate_q", generate_questions)

# Define edges (Deterministic State Machine)
workflow.set_entry_point("extract")
workflow.add_edge("extract", "translate")
workflow.add_edge("translate", "generate_q")
workflow.add_edge("generate_q", END)

# Compile the agent
bill_analyzer_app = workflow.compile()

def run_analysis(text: str):
    """Execution function to be called by FastAPI."""
    initial_state = {"document_text": text}
    result = bill_analyzer_app.invoke(initial_state)
    return result
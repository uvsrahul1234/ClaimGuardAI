from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from typing import TypedDict, Annotated, Sequence

import json
import os

# Define the State for our LangGraph
class BillState(TypedDict):
    document_text: str
    extracted_data: dict
    translated_summary: str
    suggested_questions: list[str]

load_dotenv() # This reads the .env file and sets the variables

# Initialize the Gemini model (Ensure GOOGLE_API_KEY is set in your terminal)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def extract_entities(state: BillState):
    """Simulates RAG and entity extraction to find charges and codes."""
    prompt = f"Extract total charges, out-of-network fees, and CPT codes from this bill:\n{state['document_text']}\nReturn ONLY valid JSON with keys: total_charges, unexpected_fees, cpt_codes."
    response = llm.invoke([HumanMessage(content=prompt)])
    
    try:
        # Robust validation loop concept
        extracted = json.loads(response.content.strip('```json\n').strip('```'))
    except json.JSONDecodeError:
        extracted = {"error": "Failed to parse document entities."}
        
    return {"extracted_data": extracted}

def translate_terminology(state: BillState):
    """Translates complex extracted terms into plain English."""
    data = state.get("extracted_data", {})
    prompt = f"Explain these billing entities in simple 8th-grade English: {data}"
    response = llm.invoke([HumanMessage(content=prompt)])
    
    return {"translated_summary": response.content}

def generate_questions(state: BillState):
    """Generates personalized questions for the healthcare provider."""
    data = state.get("extracted_data", {})
    prompt = f"Based on these charges: {data}, suggest 3 polite questions the patient should ask their provider to clarify the bill."
    response = llm.invoke([HumanMessage(content=prompt)])
    
    questions = response.content.split('\n')
    return {"suggested_questions": [q for q in questions if q]}

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
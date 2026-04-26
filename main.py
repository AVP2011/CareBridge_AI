# main.py

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm.model_loader import ModelLoader
from engines.post_rejection_engine import PostRejectionEngine
from engines.pre_purchase_engine import PrePurchaseEngine
from engines.policy_comparison_engine import PolicyComparisonEngine

from schemas.request import PostRejectionRequest, PrePurchaseRequest
from schemas.chat import ReportChatResponse
from schemas.policy_comparison import PolicyComparisonReport

from services.report_chat_service import run_report_chat
from services.chat_memory import create_session

import pdfplumber
import pytesseract
from PIL import Image
import io


# --------------------------------------------------
# Engine registry
# --------------------------------------------------

_engines: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model & engines at startup."""
    print("🔄 CareBridge AI starting up...")

    loader = ModelLoader()
    model, tokenizer = loader.get_model()

    _engines["post_rejection"] = PostRejectionEngine(model, tokenizer)
    _engines["pre_purchase"]   = PrePurchaseEngine(model, tokenizer)
    _engines["comparison"]     = PolicyComparisonEngine(model, tokenizer)
    _engines["model"]          = model
    _engines["tokenizer"]      = tokenizer

    print("✅ All engines ready")
    yield
    print("🔄 CareBridge AI shutting down...")


# --------------------------------------------------
# App
# --------------------------------------------------

app = FastAPI(
    title="CareBridge AI",
    version="2.0.0",
    lifespan=lifespan,
)

# --------------------------------------------------
# CORS FIX (important for localhost + ngrok)
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allows localhost & ngrok
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Health Check
# --------------------------------------------------

@app.get("/")
def health():
    return {"status": "CareBridge AI v2 running", "engines": list(_engines.keys())}


# --------------------------------------------------
# Post-Rejection Audit
# --------------------------------------------------

@app.post("/audit")
def audit(request: PostRejectionRequest):
    try:
        result = _engines["post_rejection"].run(request)
        return result.model_dump()
    except Exception as e:
        print("⚠️ /audit error:", e)
        raise HTTPException(500, "Audit engine error. Please try again.")


# --------------------------------------------------
# Pre-Purchase Analysis
# --------------------------------------------------

@app.post("/prepurchase")
def prepurchase(request: PrePurchaseRequest):
    try:
        result = _engines["pre_purchase"].run(
            request.policy_text, 
            request.provider_id, 
            request.agent_summary
        )
        return result.model_dump()
    except Exception as e:
        print("⚠️ /prepurchase error:", e)
        raise HTTPException(500, "Pre-purchase engine error. Please try again.")


# --------------------------------------------------
# Report Chat
# --------------------------------------------------

class ReportChatRequest(BaseModel):
    report_data: dict
    question: str


@app.post("/report-chat", response_model=ReportChatResponse)
def report_chat(request: ReportChatRequest):
    try:
        result = run_report_chat(
            model=_engines["model"],
            tokenizer=_engines["tokenizer"],
            report_data=request.report_data,
            user_question=request.question,
        )
        return result.model_dump()
    except Exception as e:
        print("⚠️ /report-chat error:", e)
        raise HTTPException(500, "Chat service error.")


# --------------------------------------------------
# File Upload Helpers
# --------------------------------------------------

from fastapi import Form

async def _extract_file(file: UploadFile) -> str:
    if file is None or file.filename == "":
        return ""

    try:
        content = await file.read()
        extracted_text = ""

        # Safe extraction for PDFs using RobustPDFExtractor
        if file.content_type == "application/pdf" or file.filename.lower().endswith(".pdf"):
            import uuid
            import os
            temp_file_path = f"tmp_{uuid.uuid4()}.pdf"
            with open(temp_file_path, "wb") as f:
                f.write(content)
            
            try:
                from services.pdf_extractor_robust import RobustPDFExtractor
                extractor = RobustPDFExtractor(enable_ocr=True) # Enforcing OCR per user instructions
                extracted_text, method = extractor.extract_text(temp_file_path)
                print(f"✅ Extracted {file.filename} via {method}")
            except Exception as e:
                print(f"⚠️ Robust extraction failed for {file.filename}: {e}")
                # Fallback to simple
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            extracted_text += text + "\n"
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        elif file.content_type.startswith("image/") or file.filename.lower().endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(io.BytesIO(content))
            extracted_text = pytesseract.image_to_string(image)
            print(f"✅ Extracted {file.filename} via OCR Image")

        else:
            extracted_text = content.decode("utf-8", errors="ignore")

        return extracted_text

    except Exception as e:
        print(f"⚠️ Extraction error for {file.filename}: {e}")
        return ""

# --------------------------------------------------
# Pre-Purchase File Upload Analysis
# --------------------------------------------------

@app.post("/prepurchase/upload")
async def prepurchase_upload(
    file: UploadFile = File(...),
    agent_summary: str = Form(None)
):
    try:
        extracted_text = await _extract_file(file)

        if not extracted_text.strip() or len(extracted_text) < 100:
            raise HTTPException(
                status_code=422,
                detail="Could not extract sufficient text."
            )

        result = _engines["pre_purchase"].run(
            extracted_text, 
            None, 
            agent_summary
        )
        return result.model_dump()

    except HTTPException:
        raise
    except Exception as e:
        print("⚠️ /prepurchase/upload error:", e)
        raise HTTPException(500, "File processing failed.")


# --------------------------------------------------
# Audit Rejection File Upload Analysis
# --------------------------------------------------

def _compress_audit_report(report_dict: dict) -> dict:
    # Compressing output per user instructions to avoid overwhelming the frontend
    if "weak_points" in report_dict and isinstance(report_dict["weak_points"], list):
        report_dict["weak_points"] = report_dict["weak_points"][:3]
    if "strong_points" in report_dict and isinstance(report_dict["strong_points"], list):
        report_dict["strong_points"] = report_dict["strong_points"][:3]
    if "reapplication_steps" in report_dict and isinstance(report_dict["reapplication_steps"], list):
        report_dict["reapplication_steps"] = report_dict["reapplication_steps"][:3]
    return report_dict

@app.post("/audit/upload")
async def analyze_audit_upload(
    policy_file: UploadFile = File(None),
    rejection_file: UploadFile = File(None),
    medical_file: UploadFile = File(None),
    user_explanation: str = Form(None)
):
    try:
        policy_text = await _extract_file(policy_file)
        rejection_text = await _extract_file(rejection_file)
        medical_text = await _extract_file(medical_file)

        if not policy_text.strip() and not rejection_text.strip():
             raise HTTPException(status_code=422, detail="Both Policy and Rejection Letter are required.")

        combined_input = {
            "policy_text": policy_text,
            "rejection_text": rejection_text,
            "medical_documents_text": medical_text,
            "user_explanation": user_explanation
        }

        # Structure input matching schemas/request.py PostRejectionRequest
        request_obj = PostRejectionRequest(**combined_input)
        
        result_model = _engines["post_rejection"].run(request_obj)
        report_data = result_model.model_dump()
        
        return _compress_audit_report(report_data)

    except HTTPException:
        raise
    except Exception as e:
        print("⚠️ /audit/upload error:", e)
        raise HTTPException(500, "Audit upload failed.")



# --------------------------------------------------
# Chat Session
# --------------------------------------------------

class CreateChatSessionRequest(BaseModel):
    report_data: dict


class ContinueChatRequest(BaseModel):
    session_id: str
    question: str


@app.post("/chat-session")
def create_chat_session(request: CreateChatSessionRequest):
    try:
        session_id = create_session(request.report_data)
        return {"session_id": session_id}
    except Exception as e:
        print("⚠️ /chat-session error:", e)
        raise HTTPException(500, "Failed to create chat session.")


@app.post("/chat")
def continue_chat(request: ContinueChatRequest):
    try:
        result = run_report_chat(
            model=_engines["model"],
            tokenizer=_engines["tokenizer"],
            session_id=request.session_id,
            user_question=request.question,
        )
        return result.model_dump()
    except Exception as e:
        print("⚠️ /chat error:", e)
        raise HTTPException(500, "Chat service error.")


# --------------------------------------------------
# Policy Comparison
# --------------------------------------------------

class PolicyComparisonRequest(BaseModel):
    policy_a_text: str
    policy_b_text: str


@app.post("/compare", response_model=PolicyComparisonReport)
def compare_policies(request: PolicyComparisonRequest):
    try:
        result = _engines["comparison"].compare(
            policy_a_text=request.policy_a_text,
            policy_b_text=request.policy_b_text,
        )
        return result.model_dump()
    except Exception as e:
        print("⚠️ /compare error:", e)
        raise HTTPException(500, "Comparison engine error.")
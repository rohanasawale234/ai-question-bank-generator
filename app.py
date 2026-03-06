
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import io
from fastapi import Response

from pypdf import PdfReader
# Use Platypus for professional PDF layout and text wrapping
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# THE MODERN IMPORT FOR 2026
from google import genai 

# ---------- CONFIG ----------

# 1. Replace with your key from https://aistudio.google.com/
API_KEY = "AIzaSyBP2dAVCYIwrVXmVbevk2SPo_aLRd9k5co" 

# 2. Initialize the Client (Modern SDK way)
client = genai.Client(api_key=API_KEY)
# Using the stable 2026 Flash model
MODEL_ID = "gemini-2.5-flash" 

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global list (For a real app, use a database or session)
question_bank = []

# ---------- QUESTION GENERATION ----------

import re

def generate_questions(text):

    prompt = f"""
Generate 15 exam questions based on this text.
Return only the questions, one per line without numbering.

{text}
"""

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt
        )

        questions = []

        if response.text:
            lines = response.text.strip().split("\n")

            for line in lines:
                q = line.strip()

                # remove numbering like "1. ", "2) ", "10. "
                q = re.sub(r'^\d+[\.\)]\s*', '', q)

                if len(q) > 10:
                    questions.append(q)

        return questions[:20]

    except Exception as e:
        print("Gemini API Error:", e)
        return ["Error generating questions"]

# ---------- ROUTES ----------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "questions": []})

@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, text: str = Form(...)):
    global question_bank
    question_bank = generate_questions(text)
    return templates.TemplateResponse("index.html", {"request": request, "questions": question_bank})

@app.post("/upload", response_class=HTMLResponse)
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    global question_bank
    reader = PdfReader(file.file)
    full_text = " ".join([page.extract_text() or "" for page in reader.pages])
    question_bank = generate_questions(full_text)
    return templates.TemplateResponse("index.html", {"request": request, "questions": question_bank})

@app.get("/generate-paper", response_class=HTMLResponse)
async def paper(request: Request):
    return templates.TemplateResponse("paper.html", {
        "request": request,
        "short": question_bank[:5],
        "medium": question_bank[5:10],
        "long": question_bank[10:15]
    })

@app.get("/download-bank")
async def download_pdf():
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("<b>OFFICIAL QUESTION PAPER</b>", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black))
    story.append(Spacer(1, 20))

    # Helper to add categorized questions
    def add_marks_section(title, mark_tag):
        story.append(Paragraph(f"<b>{title}</b>", styles['Heading2']))
        story.append(Spacer(1, 10))
        # Filter global question_bank
        qs = [q.split('] ')[1] for q in question_bank if mark_tag in q]
        for i, q_text in enumerate(qs):
            # Using Paragraph handles long text wrapping automatically
            story.append(Paragraph(f"{i+1}. {q_text}", styles['Normal']))
            story.append(Spacer(1, 12))
        story.append(Spacer(1, 15))

    add_marks_section("Section A (2 Marks Each)", "[2 Marks]")
    add_marks_section("Section B (3 Marks Each)", "[3 Marks]")
    add_marks_section("Section C (4 Marks Each)", "[4 Marks]")
    add_marks_section("Section D (5 Marks Each)", "[5 Marks]")

    doc.build(story)
    
    # Prepare the response
    pdf_out = buffer.getvalue()
    buffer.close()
    
    headers = {'Content-Disposition': 'attachment; filename="Question_Paper.pdf"'}
    return Response(content=pdf_out, media_type="application/pdf", headers=headers)
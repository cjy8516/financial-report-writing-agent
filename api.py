# api.py
from fastapi import FastAPI
from pydantic import BaseModel
from agent_core import run_analysis

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporary; lock down later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    task: str
    competitors: list[str]
    csv_file: str
    max_revisions: int = 2

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    report = run_analysis(req.task, req.competitors, req.csv_file, req.max_revisions)
    return {"report": report}

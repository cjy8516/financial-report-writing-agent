# api.py
from fastapi import FastAPI
from pydantic import BaseModel
from agent_core import run_analysis

app = FastAPI()

class AnalyzeRequest(BaseModel):
    task: str
    competitors: list[str]
    csv_file: str
    max_revisions: int = 2

@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    report = run_analysis(req.task, req.competitors, req.csv_file, req.max_revisions)
    return {"report": report}
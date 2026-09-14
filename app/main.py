from fastapi import FastAPI, HTTPException
from .service import (
    FraudRequest, FeedbackRequest, AnalysisUnavailable,
    analyze_fraud as run_analysis, feedback as record_feedback,
)

app = FastAPI(title='CyberShield Fraud Detection Agent', version='2.1.0')


@app.get('/')
def home():
    return {'message': 'CyberShield AI Agent is running', 'status': 'active'}


@app.post('/analyze')
def analyze_fraud(request: FraudRequest):
    try:
        return run_analysis(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except AnalysisUnavailable as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post('/feedback')
def feedback(request: FeedbackRequest):
    try:
        return record_feedback(request)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

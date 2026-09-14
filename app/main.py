from typing import Literal, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator

from .agent import fraud_agent
from .images import prepare_image
from .storage import record_assessment, save_feedback
from .urls import check_urls

app = FastAPI(title='CyberShield Fraud Detection Agent', version='2.0.0')


class FraudRequest(BaseModel):
    message: str = Field(default='', max_length=10000)
    language: Literal['English', 'Hindi', 'Hinglish'] = 'English'
    image_base64: Optional[str] = Field(default=None, max_length=6990508)

    @model_validator(mode='after')
    def has_content(self):
        self.message = self.message.strip()
        if not self.message and not self.image_base64:
            raise ValueError('Enter a message or upload a screenshot.')
        return self


class FeedbackRequest(BaseModel):
    analysis_id: UUID
    rating: Literal['helpful', 'not_helpful']


@app.get('/')
def home():
    return {'message': 'CyberShield AI Agent is running', 'status': 'active'}


@app.post('/analyze')
def analyze_fraud(request: FraudRequest):
    try:
        image = prepare_image(request.image_base64)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    try:
        result = fraud_agent.invoke({'user_message': request.message, 'language': request.language,
                                     'image': image, 'analysis': None})
    except Exception as exc:
        raise HTTPException(status_code=502, detail='Gemini analysis failed. Check your API key, model access, quota, and connection, then retry.') from exc
    analysis = result['analysis']
    urls = check_urls(request.message + '\n' + analysis.get('extracted_text', ''))
    return {'success': True, 'analysis_id': record_assessment(analysis['risk_level']),
            'analysis': analysis, 'url_checks': urls}


@app.post('/feedback')
def feedback(request: FeedbackRequest):
    if not save_feedback(str(request.analysis_id), request.rating):
        raise HTTPException(status_code=404, detail='Assessment not found.')
    return {'success': True}

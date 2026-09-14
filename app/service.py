from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from .agent import fraud_agent
from .images import prepare_image
from .storage import record_assessment, save_feedback
from .urls import check_urls



class AnalysisUnavailable(RuntimeError):
    pass


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


def analyze_fraud(request: FraudRequest):
    try:
        image = prepare_image(request.image_base64)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    try:
        result = fraud_agent.invoke({'user_message': request.message, 'language': request.language,
                                     'image': image, 'analysis': None})
    except Exception as exc:
        raise AnalysisUnavailable('Gemini analysis failed. Check GOOGLE_API_KEY in Streamlit Secrets (or local .env), model access, quota, and connection, then retry.') from exc
    analysis = result['analysis']
    urls = check_urls(request.message + '\n' + analysis.get('extracted_text', ''))
    return {'success': True, 'analysis_id': record_assessment(analysis['risk_level']),
            'analysis': analysis, 'url_checks': urls}


def feedback(request: FeedbackRequest):
    if not save_feedback(str(request.analysis_id), request.rating):
        raise LookupError('Assessment not found.')
    return {'success': True}

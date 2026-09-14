from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class FraudAnalysis(BaseModel):
    risk_level: Literal['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    fraud_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated probability that the input is fraudulent",
    )
    fraud_type: str = Field(
        description="Phishing, Smishing, Vishing, Scam, Identity Theft, Payment Fraud, Malware, or Unknown"
    )
    summary: str
    indicators: List[str]
    recommendation: str
    needs_more_information: bool
    follow_up_question: Optional[str] = None
    extracted_text: str = Field(default='', description='Visible screenshot text in its original language. Empty if no screenshot; never invent unreadable text.')

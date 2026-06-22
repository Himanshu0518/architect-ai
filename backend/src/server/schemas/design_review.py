from pydantic import BaseModel, Field
from typing import List, Literal


class Issue(BaseModel):
    severity: Literal["critical", "high", "medium", "low"] = Field(..., description="Severity level of the issue")
    component: str = Field(..., description="Which component this issue relates to")
    issue: str = Field(..., description="Description of the problem")
    recommendation: str = Field(..., description="Actionable recommendation to resolve it")


class ScalabilityAssessment(BaseModel):
    bottlenecks: List[str] = Field(..., description="Identified scalability bottlenecks")
    recommendations: List[str] = Field(..., description="Recommendations to address them")


class ReliabilityAssessment(BaseModel):
    single_points_of_failure: List[str] = Field(..., description="Identified SPOFs")
    recommendations: List[str] = Field(..., description="Recommendations to address them")


class SecurityAssessment(BaseModel):
    gaps: List[str] = Field(..., description="Identified security gaps")
    recommendations: List[str] = Field(..., description="Security hardening recommendations")


class CostAssessment(BaseModel):
    estimated_monthly_usd: str = Field(..., description="Rough monthly cost range, e.g. '$5,000 - $15,000'")
    cost_optimizations: List[str] = Field(..., description="Specific cost reduction strategies")


class DesignReview(BaseModel):
    """
    Output contract for ReviewCrew.
    Contains a scored critique of the complete system design.
    """

    overall_score: float = Field(..., ge=1, le=10, description="Overall design quality score from 1 to 10")
    strengths: List[str] = Field(..., description="What the design does well")
    issues: List[Issue]
    scalability_assessment: ScalabilityAssessment
    reliability_assessment: ReliabilityAssessment
    security_assessment: SecurityAssessment
    cost_assessment: CostAssessment
    final_recommendations: List[str] = Field(..., description="Top-level recommendations for the team")

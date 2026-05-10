from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any, Literal
from enum import Enum

class IssueType(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class DeviceType(str, Enum):
    MOBILE = "mobile"
    TABLET = "tablet"
    DESKTOP = "desktop"
    FOUR_K = "4k"
    LARGE_DESKTOP = "large-desktop"
    ALL = "all"
    GUIDE = "guide"

class AnalysisStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    ERROR = "error"

class RecommendationCategory(str, Enum):
    CSS = "css"
    HTML = "html"
    ACCESSIBILITY = "accessibility"
    PERFORMANCE = "performance"
    UX = "ux"

class Priority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Request Models
class AnalysisRequest(BaseModel):
    url: str = Field(..., description="URL to analyze")

# Response Models
class AnalysisResponse(BaseModel):
    analysis_id: str
    message: str
    status: str

# Data Models
class ScreenshotData(BaseModel):
    id: str
    device: str
    resolution: str
    url: str
    full_page_url: Optional[str] = None
    compliant: Optional[bool] = None
    violations: List[Dict[str, Any]] = []

class Issue(BaseModel):
    id: str
    type: IssueType
    severity: int = Field(ge=1, le=5)
    title: str
    description: str
    device: DeviceType
    element: Optional[str] = None
    suggestion: Optional[str] = None

class Recommendation(BaseModel):
    id: str
    category: RecommendationCategory
    title: str
    description: str
    justification: Optional[str] = None
    code_example: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None
    documentation: Optional[str] = None
    priority: Priority

class Score(BaseModel):
    mobile: int = Field(ge=0, le=100)
    tablet: int = Field(ge=0, le=100)
    desktop: int = Field(ge=0, le=100)
    overall: int = Field(ge=0, le=100)

class TechnologyInfo(BaseModel):
    frameworks: List[str] = []
    cms: Optional[str] = None
    libraries: List[str] = []
    languages: List[str] = []
    server: Optional[str] = None

class SeoMeta(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[str] = None
    robots: Optional[str] = None
    canonical: Optional[str] = None
    og: Dict[str, str] = {}
    twitter: Dict[str, str] = {}

class AnalysisStatus(BaseModel):
    id: str
    url: str
    status: AnalysisStatus
    created_at: datetime
    progress: int = Field(ge=0, le=100)
    message: str = ""
    screenshots: List[ScreenshotData] = []
    issues: List[Issue] = []
    recommendations: List[Recommendation] = []
    score: Score = Field(default_factory=lambda: Score(mobile=0, tablet=0, desktop=0, overall=0))
    summary: str = ""
    error: Optional[str] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    technology: Optional[TechnologyInfo] = None
    seo: Optional[SeoMeta] = None
    guide: Optional[Dict[str, Any]] = None

    @classmethod
    def from_db_model(cls, db_model):
        """Convert database model to API model"""
        return cls(
            id=db_model.id,
            url=db_model.url,
            status=db_model.status,
            created_at=db_model.created_at,
            progress=db_model.progress,
            message=db_model.message or "",
            screenshots=db_model.screenshots or [],
            issues=db_model.issues or [],
            recommendations=db_model.recommendations or [],
            score=Score(**db_model.score) if db_model.score else Score(),
            summary=db_model.summary or "",
            error=db_model.error,
            technology=None,
            seo=None
        )

# Database Models (for reference)
class AnalysisDB(BaseModel):
    id: str = Field(primary_key=True)
    url: str
    status: str
    created_at: datetime
    updated_at: datetime
    progress: int = 0
    message: Optional[str] = None
    screenshots: Optional[List[Dict[str, Any]]] = None
    issues: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    score: Optional[Dict[str, int]] = None
    summary: Optional[str] = None
    error: Optional[str] = None

class ScreenshotDB(BaseModel):
    id: str = Field(primary_key=True)
    analysis_id: str = Field(foreign_key="analyses.id")
    device: str
    resolution: str
    filename: str
    full_page_filename: str
    created_at: datetime

class IssueDB(BaseModel):
    id: str = Field(primary_key=True)
    analysis_id: str = Field(foreign_key="analyses.id")
    type: str
    severity: int
    title: str
    description: str
    device: str
    element: Optional[str] = None
    suggestion: Optional[str] = None
    created_at: datetime

class RecommendationDB(BaseModel):
    id: str = Field(primary_key=True)
    analysis_id: str = Field(foreign_key="analyses.id")
    category: str
    title: str
    description: str
    code_example: Optional[str] = None
    before: Optional[str] = None
    after: Optional[str] = None
    documentation: Optional[str] = None
    priority: str
    created_at: datetime

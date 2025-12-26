import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
import uuid

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///responsive_tests.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Database Models
class Analysis(Base):
    __tablename__ = "analyses"
    
    id = Column(String, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    progress = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    screenshots = Column(JSON, nullable=True)
    issues = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)
    score = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

class Screenshot(Base):
    __tablename__ = "screenshots"
    
    id = Column(String, primary_key=True, index=True)
    analysis_id = Column(String, nullable=False, index=True)
    device = Column(String, nullable=False)
    resolution = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    full_page_filename = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Issue(Base):
    __tablename__ = "issues"
    
    id = Column(String, primary_key=True, index=True)
    analysis_id = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    severity = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    device = Column(String, nullable=False)
    element = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(String, primary_key=True, index=True)
    analysis_id = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    code_example = Column(Text, nullable=True)
    before = Column(Text, nullable=True)
    after = Column(Text, nullable=True)
    documentation = Column(String, nullable=True)
    priority = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        
    async def initialize(self):
        """Initialize database tables"""
        try:
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created successfully")
            
        except Exception as e:
            print(f"Error creating database tables: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        try:
            self.engine.dispose()
            print("Database connection closed")
        except Exception as e:
            print(f"Error closing database connection: {e}")
    
    def get_session(self) -> Session:
        """Get database session"""
        return SessionLocal()
    
    async def save_analysis(
        self,
        analysis_id: str,
        url: str,
        status: str,
        screenshots: List[Dict[str, Any]] = None,
        issues: List[Dict[str, Any]] = None,
        recommendations: List[Dict[str, Any]] = None,
        score: Dict[str, int] = None,
        summary: str = None,
        error: str = None
    ) -> bool:
        """Save analysis results to database"""
        session = self.get_session()
        try:
            # Check if analysis exists
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            
            if analysis:
                # Update existing analysis
                analysis.status = status
                analysis.url = url
                analysis.updated_at = datetime.utcnow()
                analysis.screenshots = screenshots
                analysis.issues = issues
                analysis.recommendations = recommendations
                analysis.score = score
                analysis.summary = summary
                analysis.error = error
            else:
                # Create new analysis
                analysis = Analysis(
                    id=analysis_id,
                    url=url,
                    status=status,
                    screenshots=screenshots,
                    issues=issues,
                    recommendations=recommendations,
                    score=score,
                    summary=summary,
                    error=error
                )
                session.add(analysis)
            
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error saving analysis: {e}")
            return False
        finally:
            session.close()
    
    async def get_analysis(self, analysis_id: str) -> Optional[Analysis]:
        """Get analysis by ID"""
        session = self.get_session()
        try:
            analysis = session.query(Analysis).filter(Analysis.id == analysis_id).first()
            return analysis
        except Exception as e:
            print(f"Error getting analysis: {e}")
            return None
        finally:
            session.close()
    
    async def get_recent_analyses(self, limit: int = 10) -> List[Analysis]:
        """Get recent analyses"""
        session = self.get_session()
        try:
            analyses = session.query(Analysis).order_by(Analysis.created_at.desc()).limit(limit).all()
            return analyses
        except Exception as e:
            print(f"Error getting recent analyses: {e}")
            return []
        finally:
            session.close()
    
    async def save_screenshot(
        self,
        analysis_id: str,
        device: str,
        resolution: str,
        filename: str,
        full_page_filename: str
    ) -> bool:
        """Save screenshot information to database"""
        session = self.get_session()
        try:
            screenshot = Screenshot(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                device=device,
                resolution=resolution,
                filename=filename,
                full_page_filename=full_page_filename
            )
            session.add(screenshot)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error saving screenshot: {e}")
            return False
        finally:
            session.close()
    
    async def get_screenshots(self, analysis_id: str) -> List[Screenshot]:
        """Get screenshots for an analysis"""
        session = self.get_session()
        try:
            screenshots = session.query(Screenshot).filter(Screenshot.analysis_id == analysis_id).all()
            return screenshots
        except Exception as e:
            print(f"Error getting screenshots: {e}")
            return []
        finally:
            session.close()
    
    async def save_issue(
        self,
        analysis_id: str,
        issue_type: str,
        severity: int,
        title: str,
        description: str,
        device: str,
        element: Optional[str] = None,
        suggestion: Optional[str] = None
    ) -> bool:
        """Save issue to database"""
        session = self.get_session()
        try:
            issue = Issue(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                type=issue_type,
                severity=severity,
                title=title,
                description=description,
                device=device,
                element=element,
                suggestion=suggestion
            )
            session.add(issue)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error saving issue: {e}")
            return False
        finally:
            session.close()
    
    async def save_recommendation(
        self,
        analysis_id: str,
        category: str,
        title: str,
        description: str,
        code_example: Optional[str] = None,
        before: Optional[str] = None,
        after: Optional[str] = None,
        documentation: Optional[str] = None,
        priority: str = "medium"
    ) -> bool:
        """Save recommendation to database"""
        session = self.get_session()
        try:
            recommendation = Recommendation(
                id=str(uuid.uuid4()),
                analysis_id=analysis_id,
                category=category,
                title=title,
                description=description,
                code_example=code_example,
                before=before,
                after=after,
                documentation=documentation,
                priority=priority
            )
            session.add(recommendation)
            session.commit()
            return True
            
        except Exception as e:
            session.rollback()
            print(f"Error saving recommendation: {e}")
            return False
        finally:
            session.close()
    
    async def get_issues(self, analysis_id: str) -> List[Issue]:
        """Get issues for an analysis"""
        session = self.get_session()
        try:
            issues = session.query(Issue).filter(Issue.analysis_id == analysis_id).all()
            return issues
        except Exception as e:
            print(f"Error getting issues: {e}")
            return []
        finally:
            session.close()
    
    async def get_recommendations(self, analysis_id: str) -> List[Recommendation]:
        """Get recommendations for an analysis"""
        session = self.get_session()
        try:
            recommendations = session.query(Recommendation).filter(Recommendation.analysis_id == analysis_id).all()
            return recommendations
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            return []
        finally:
            session.close()

# Global database manager instance
db_manager = DatabaseManager()

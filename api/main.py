from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

from agent.responsive_agent import ResponsiveTestingAgent
from database.database import DatabaseManager
from models.models import (
    AnalysisRequest, AnalysisResponse, ScreenshotData, 
    Issue, Recommendation, AnalysisStatus
)

# Initialize FastAPI app
app = FastAPI(
    title="Responsive Testing API",
    description="API para análise de responsividade de sites com IA",
    version="1.0.0"
)

# Configure CORS
load_dotenv()
_cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175")
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories for screenshots and reports
SCREENSHOTS_DIR = Path("screenshots")
REPORTS_DIR = Path("reports")
SCREENSHOTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/screenshots", StaticFiles(directory="screenshots"), name="screenshots")
app.mount("/reports", StaticFiles(directory="reports"), name="reports")

# Initialize services
db_manager = DatabaseManager()
agent = ResponsiveTestingAgent()

# Store for active analyses (in production, use Redis or similar)
active_analyses: Dict[str, AnalysisStatus] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize database and services"""
    try:
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        await db_manager.initialize()
        print("Database initialized")
        
        install_pw = os.getenv("PLAYWRIGHT_INSTALL_ON_STARTUP", "false").lower() == "true"
        if install_pw:
            os.system("playwright install chromium")
            print("Playwright browsers installed")
        
    except Exception as e:
        print(f"Error during startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources"""
    try:
        await db_manager.close()
        print("Database connection closed")
    except Exception as e:
        print(f"Error during shutdown: {e}")

@app.post("/api/analyze", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """Start a new responsive analysis"""
    try:
        # Generate unique analysis ID
        analysis_id = str(uuid.uuid4())
        
        # Create initial status
        status = AnalysisStatus(
            id=analysis_id,
            url=request.url,
            status="pending",
            created_at=datetime.now(),
            progress=0,
            message="Iniciando análise..."
        )
        
        # Store in active analyses
        active_analyses[analysis_id] = status
        
        # Add analysis task to background
        background_tasks.add_task(process_analysis, analysis_id, request.url)
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            message="Análise iniciada com sucesso",
            status="pending"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao iniciar análise: {str(e)}")

@app.get("/api/analysis/{analysis_id}", response_model=AnalysisStatus)
async def get_analysis_status(analysis_id: str):
    """Get analysis status and results"""
    try:
        # Check if it's an active analysis
        if analysis_id in active_analyses:
            return active_analyses[analysis_id]
        
        # Otherwise, try to get from database
        analysis = await db_manager.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Análise não encontrada")
        
        return AnalysisStatus.from_db_model(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter análise: {str(e)}")

@app.get("/api/screenshots/{analysis_id}")
async def get_screenshots(analysis_id: str):
    """Get screenshots for an analysis"""
    try:
        # Get analysis from database
        analysis = await db_manager.get_analysis(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Análise não encontrada")
        
        # Get screenshots
        screenshots = await db_manager.get_screenshots(analysis_id)
        
        # Return screenshot URLs
        screenshot_urls = []
        for screenshot in screenshots:
            screenshot_urls.append({
                "id": screenshot.id,
                "device": screenshot.device,
                "resolution": screenshot.resolution,
                "url": f"/screenshots/{screenshot.filename}",
                "full_page_url": f"/screenshots/{screenshot.full_page_filename}"
            })
        
        return screenshot_urls
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter screenshots: {str(e)}")

@app.get("/api/history")
async def get_analysis_history(limit: int = 10):
    """Get recent analysis history"""
    try:
        analyses = await db_manager.get_recent_analyses(limit)
        return [AnalysisStatus.from_db_model(analysis) for analysis in analyses]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter histórico: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "active_analyses": len(active_analyses)
    }

async def process_analysis(analysis_id: str, url: str):
    """Process the responsive analysis"""
    try:
        print(f"Starting analysis {analysis_id} for {url}")
        
        # Update status
        active_analyses[analysis_id].status = "analyzing"
        active_analyses[analysis_id].progress = 10
        active_analyses[analysis_id].message = "Capturando screenshots..."
        
        # Step 1: Capture screenshots
        screenshots: List[Dict[str, Any]] = []
        try:
            screenshots = await agent.capture_screenshots(url, analysis_id)
            active_analyses[analysis_id].progress = 25
            active_analyses[analysis_id].message = "Analisando layout..."
        except Exception as e:
            active_analyses[analysis_id].message = f"Falha ao capturar screenshots: {type(e).__name__}: {e}"
            screenshots = []
            active_analyses[analysis_id].progress = 20
        
        # Step 2: Analyze layout
        layout_issues = await agent.analyze_layout(url, screenshots)
        active_analyses[analysis_id].progress = 50
        active_analyses[analysis_id].message = "Analisando visual..."
        
        # Step 3: Visual analysis with AI
        visual_issues = await agent.analyze_with_vision(screenshots)
        active_analyses[analysis_id].progress = 75
        active_analyses[analysis_id].message = "Gerando recomendações..."
        
        # Step 4: Generate recommendations and report
        all_issues = layout_issues + visual_issues
        recommendations = await agent.generate_suggestions(all_issues)
        report_data = await agent.create_report(
            analysis_id, url, screenshots, all_issues, recommendations
        )
        
        # Calculate scores
        scores = calculate_scores(all_issues)
        
        # Update final status
        active_analyses[analysis_id].status = "completed"
        active_analyses[analysis_id].progress = 100
        active_analyses[analysis_id].message = "Análise concluída"
        active_analyses[analysis_id].screenshots = screenshots
        active_analyses[analysis_id].issues = all_issues
        active_analyses[analysis_id].recommendations = recommendations
        active_analyses[analysis_id].score = scores
        active_analyses[analysis_id].summary = report_data.get("summary", "")
        
        # Save to database
        await save_analysis_to_db(analysis_id, active_analyses[analysis_id])
        
        print(f"Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        print(f"Error in analysis {analysis_id}: {type(e).__name__}: {e}")
        
        # Update status with error
        if analysis_id in active_analyses:
            active_analyses[analysis_id].status = "error"
            active_analyses[analysis_id].message = f"Erro na análise: {type(e).__name__}: {e}"
            active_analyses[analysis_id].error = f"{type(e).__name__}: {e}"

def calculate_scores(issues: List[Issue]) -> Dict[str, int]:
    """Calculate responsive scores based on issues"""
    try:
        # Count issues by severity and device
        critical_count = len([i for i in issues if i.type == "critical"])
        warning_count = len([i for i in issues if i.type == "warning"])
        info_count = len([i for i in issues if i.type == "info"])
        
        # Calculate base score (start from 100)
        base_score = 100
        
        # Deduct points for issues
        score_deduction = (critical_count * 15) + (warning_count * 8) + (info_count * 3)
        overall_score = max(0, base_score - score_deduction)
        
        # Calculate device-specific scores (simplified)
        mobile_score = max(0, overall_score - len([i for i in issues if i.device == "mobile" and i.type == "critical"]) * 10)
        tablet_score = max(0, overall_score - len([i for i in issues if i.device == "tablet" and i.type == "critical"]) * 10)
        desktop_score = max(0, overall_score - len([i for i in issues if i.device == "desktop" and i.type == "critical"]) * 10)
        
        return {
            "mobile": mobile_score,
            "tablet": tablet_score,
            "desktop": desktop_score,
            "overall": overall_score
        }
        
    except Exception as e:
        print(f"Error calculating scores: {e}")
        return {
            "mobile": 0,
            "tablet": 0,
            "desktop": 0,
            "overall": 0
        }

async def save_analysis_to_db(analysis_id: str, status: AnalysisStatus):
    """Save analysis results to database"""
    try:
        await db_manager.save_analysis(
            analysis_id=analysis_id,
            url=status.url,
            status=status.status,
            screenshots=status.screenshots,
            issues=status.issues,
            recommendations=status.recommendations,
            score=status.score,
            summary=status.summary
        )
        print(f"Analysis {analysis_id} saved to database")
        
    except Exception as e:
        print(f"Error saving analysis to database: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

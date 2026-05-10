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
from dotenv import load_dotenv, find_dotenv

from agent.responsive_agent import ResponsiveTestingAgent
from database.database import DatabaseManager
from models.models import (
    AnalysisRequest, AnalysisResponse, ScreenshotData, 
    Issue, Recommendation, AnalysisStatus
)

# Initialize FastAPI app
if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

app = FastAPI(
    title="Responsive Testing API",
    description="API para análise de responsividade de sites com IA",
    version="1.0.0"
)

# Configure CORS
load_dotenv(find_dotenv())
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
API_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_DIR.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"
REPORTS_DIR = PROJECT_ROOT / "reports"
SCREENSHOTS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/screenshots", StaticFiles(directory=str(SCREENSHOTS_DIR)), name="screenshots")
app.mount("/reports", StaticFiles(directory=str(REPORTS_DIR)), name="reports")

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
        
        # Load responsive guide (mandatory)
        guide = agent.load_responsive_guide()

        def _normalize_devices_from_guide(guide_obj: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
            bps = (guide_obj or {}).get("breakpoints")
            if isinstance(bps, list) and len(bps) > 0:
                return bps
            return [
                {"id": "mobile", "label": "Mobile", "width": 375, "height": 667},
                {"id": "tablet", "label": "Tablet", "width": 768, "height": 1024},
                {"id": "desktop", "label": "Desktop", "width": 1024, "height": 900},
                {"id": "large-desktop", "label": "Large Desktop", "width": 1440, "height": 900},
            ]

        def _generate_placeholder_screenshots(
            analysis_id: str,
            devices: List[Dict[str, Any]],
            reason: str
        ) -> List[Dict[str, Any]]:
            from PIL import Image, ImageDraw

            screenshots: List[Dict[str, Any]] = []
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reason_str = str(reason or "")
            if len(reason_str) > 180:
                reason_str = reason_str[:180] + "..."

            for device in devices:
                device_id = device.get("id") or device.get("name") or "breakpoint"
                label = device.get("label") or str(device_id)
                w = int(device.get("width") or 0) or 800
                h = int(device.get("height") or 0) or 600
                filename = f"{analysis_id}_{device_id}_{timestamp}.png"
                full_page_filename = f"{analysis_id}_{device_id}_full_{timestamp}.png"

                img = Image.new("RGB", (w, h), color=(245, 245, 245))
                draw = ImageDraw.Draw(img)
                draw.multiline_text(
                    (20, 20),
                    f"{label}\n{w}x{h}\n(placeholder)\n{reason_str}",
                    fill=(60, 60, 60),
                )
                img.save(SCREENSHOTS_DIR / filename)
                img.save(SCREENSHOTS_DIR / full_page_filename)

                screenshots.append({
                    "id": str(uuid.uuid4()),
                    "device": str(device_id),
                    "resolution": f"{w}x{h}",
                    "url": f"/screenshots/{filename}",
                    "full_page_url": f"/screenshots/{full_page_filename}",
                    "compliant": False,
                    "violations": [{
                        "id": "screenshot_capture_failed",
                        "title": "Falha ao capturar screenshot",
                        "description": reason_str,
                        "guide_ref": "responsive-guide.md §10.2"
                    }]
                })

            return screenshots

        # Update status
        active_analyses[analysis_id].status = "analyzing"
        active_analyses[analysis_id].progress = 10
        active_analyses[analysis_id].message = "Capturando screenshots..."
        active_analyses[analysis_id].guide = guide
        
        # Step 1: Capture screenshots
        screenshots: List[Dict[str, Any]] = []
        try:
            screenshots = await agent.capture_screenshots(
                url,
                analysis_id,
                breakpoints=guide.get("breakpoints"),
                guide_rules=guide.get("rules"),
            )
            if not screenshots:
                screenshots = _generate_placeholder_screenshots(
                    analysis_id,
                    _normalize_devices_from_guide(guide),
                    "Captura retornou lista vazia."
                )

            expected = {bp.get("id") for bp in (guide.get("breakpoints") or []) if bp.get("id")}
            got = {s.get("device") for s in (screenshots or []) if s.get("device")}
            missing = sorted(list(expected - got))
            if missing:
                screenshots = screenshots or []
                screenshots.append({
                    "id": str(uuid.uuid4()),
                    "device": "guide",
                    "resolution": "",
                    "url": "",
                    "full_page_url": None,
                    "compliant": False,
                    "violations": [{
                        "id": "breakpoints_missing",
                        "title": "Breakpoints não capturados",
                        "description": f"Não foi possível capturar screenshots para: {', '.join(missing)}.",
                        "guide_ref": "responsive-guide.md §10.2"
                    }]
                })
            active_analyses[analysis_id].progress = 25
            active_analyses[analysis_id].message = "Analisando layout..."
        except Exception as e:
            reason = f"{type(e).__name__}: {e}"
            active_analyses[analysis_id].message = f"Falha ao capturar screenshots: {reason}. Gerando placeholders..."
            screenshots = _generate_placeholder_screenshots(
                analysis_id,
                _normalize_devices_from_guide(guide),
                reason
            )
            active_analyses[analysis_id].progress = 25
        

        # Convert guide violations into issues
        guide_issues: List[Dict[str, Any]] = []
        for sc in screenshots or []:
            device = sc.get("device", "all")
            for v in sc.get("violations") or []:
                vid = v.get("id", "")
                issue_type = "critical" if vid.startswith("viewport_") else "warning"
                severity = 5 if issue_type == "critical" else 3
                guide_issues.append({
                    "id": str(uuid.uuid4()),
                    "type": issue_type,
                    "severity": severity,
                    "title": v.get("title", "Não conformidade"),
                    "description": v.get("description", ""),
                    "device": device if device else "all",
                    "suggestion": f"Referência: {v.get('guide_ref', 'responsive-guide.md')}"
                })
        
        # Step 2: Analyze layout
        layout_issues = await agent.analyze_layout(url, screenshots)
        active_analyses[analysis_id].progress = 50
        active_analyses[analysis_id].message = "Analisando visual..."
        
        # Step 3: Visual analysis with AI
        visual_issues = await agent.analyze_with_vision(screenshots)
        active_analyses[analysis_id].progress = 75
        active_analyses[analysis_id].message = "Gerando recomendações..."

        # Detect technology and SEO
        tech_seo = await agent.detect_technology(url)
        
        # Step 4: Generate recommendations and report
        all_issues = guide_issues + layout_issues + visual_issues
        recommendations = await agent.generate_suggestions(all_issues)
        report_data = await agent.create_report(
            analysis_id, url, screenshots, all_issues, recommendations,
            technology=tech_seo.get('technology'), seo=tech_seo.get('seo'), guide=guide
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
        active_analyses[analysis_id].technology = tech_seo.get('technology')
        active_analyses[analysis_id].seo = tech_seo.get('seo')
        
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

def calculate_scores(issues: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate responsive scores based on issues"""
    try:
        # Count issues by severity and device
        critical_count = len([i for i in issues if i.get("type") == "critical"])
        warning_count = len([i for i in issues if i.get("type") == "warning"])
        info_count = len([i for i in issues if i.get("type") == "info"])
        
        # Calculate base score (start from 100)
        base_score = 100
        
        # Deduct points for issues
        score_deduction = (critical_count * 15) + (warning_count * 8) + (info_count * 3)
        overall_score = max(0, base_score - score_deduction)
        
        # Calculate device-specific scores (simplified)
        mobile_score = max(0, overall_score - len([i for i in issues if i.get("device") == "mobile" and i.get("type") == "critical"]) * 10)
        tablet_score = max(0, overall_score - len([i for i in issues if i.get("device") == "tablet" and i.get("type") == "critical"]) * 10)
        desktop_score = max(0, overall_score - len([i for i in issues if i.get("device") == "desktop" and i.get("type") == "critical"]) * 10)
        
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

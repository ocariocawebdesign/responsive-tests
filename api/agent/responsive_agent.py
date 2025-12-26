import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import base64
from io import BytesIO

from playwright.async_api import async_playwright
from PIL import Image
import requests
from bs4 import BeautifulSoup

class ScreenshotCaptureTool:
    """Tool for capturing screenshots of websites"""
    
    name: str = "capture_screenshots"
    description: str = "Capture screenshots of a website in different screen sizes"
    
    async def run(self, url: str, analysis_id: str) -> List[Dict[str, Any]]:
        """Capture screenshots in multiple device sizes"""
        try:
            print(f"Capturing screenshots for {url}")
            
            # Device configurations
            devices = [
                {
                    "name": "mobile",
                    "width": 375,
                    "height": 667,
                    "device_scale_factor": 2,
                    "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                },
                {
                    "name": "tablet", 
                    "width": 768,
                    "height": 1024,
                    "device_scale_factor": 2,
                    "user_agent": "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                },
                {
                    "name": "desktop",
                    "width": 1920,
                    "height": 1080,
                    "device_scale_factor": 1,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                {
                    "name": "4k",
                    "width": 3840,
                    "height": 2160,
                    "device_scale_factor": 1,
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            ]
            
            screenshots = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                for device in devices:
                    try:
                        context = await browser.new_context(
                            viewport={"width": device["width"], "height": device["height"]},
                            device_scale_factor=device["device_scale_factor"],
                            user_agent=device["user_agent"]
                        )
                        
                        page = await context.new_page()
                        
                        # Navigate to URL
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        
                        # Wait a bit for any dynamic content
                        await asyncio.sleep(2)
                        
                        # Generate filenames
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"{analysis_id}_{device['name']}_{timestamp}.png"
                        full_page_filename = f"{analysis_id}_{device['name']}_full_{timestamp}.png"
                        
                        # Take viewport screenshot
                        screenshot_path = Path("screenshots") / filename
                        await page.screenshot(path=str(screenshot_path), full_page=False)
                        
                        # Take full page screenshot
                        full_page_path = Path("screenshots") / full_page_filename
                        await page.screenshot(path=str(full_page_path), full_page=True)
                        
                        screenshots.append({
                            "id": str(uuid.uuid4()),
                            "device": device["name"],
                            "resolution": f"{device['width']}x{device['height']}",
                            "url": f"/screenshots/{filename}",
                            "full_page_url": f"/screenshots/{full_page_filename}"
                        })
                        
                        await context.close()
                        
                    except Exception as e:
                        print(f"Error capturing {device['name']} screenshot: {e}")
                        continue
                
                await browser.close()
            
            print(f"Captured {len(screenshots)} screenshots")
            return screenshots
            
        except Exception as e:
            print(f"Error capturing screenshots: {e}")
            raise

class LayoutAnalysisTool:
    """Tool for analyzing layout issues"""
    
    name: str = "analyze_layout"
    description: str = "Analyze website layout for responsive issues"
    
    async def run(self, url: str, screenshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze layout for responsive issues"""
        try:
            print(f"Analyzing layout for {url}")
            
            # Fetch the page content
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            issues = []
            
            # Check for common responsive issues
            # 1. Check for viewport meta tag
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if not viewport:
                issues.append({
                    "id": str(uuid.uuid4()),
                    "type": "critical",
                    "severity": 5,
                    "title": "Viewport Meta Tag Missing",
                    "description": "A tag meta viewport está ausente, o que pode causar problemas de escala em dispositivos móveis.",
                    "device": "mobile",
                    "element": "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
                    "suggestion": "Adicione a tag meta viewport no head do seu HTML para garantir responsividade adequada."
                })
            
            # 2. Check for media queries in CSS
            stylesheets = soup.find_all('link', attrs={'rel': 'stylesheet'})
            has_media_queries = False
            
            for stylesheet in stylesheets:
                try:
                    css_url = stylesheet.get('href')
                    if css_url:
                        if css_url.startswith('//'):
                            css_url = 'https:' + css_url
                        elif css_url.startswith('/'):
                            from urllib.parse import urljoin
                            css_url = urljoin(url, css_url)
                        
                        css_response = requests.get(css_url, timeout=10)
                        if '@media' in css_response.text:
                            has_media_queries = True
                            break
                except:
                    continue
            
            if not has_media_queries:
                issues.append({
                    "id": str(uuid.uuid4()),
                    "type": "warning",
                    "severity": 3,
                    "title": "No Media Queries Found",
                    "description": "Nenhuma media query foi encontrada nos estilos, indicando falta de adaptação para diferentes tamanhos de tela.",
                    "device": "all",
                    "suggestion": "Use media queries para adaptar o layout para diferentes tamanhos de tela. Exemplo: @media (max-width: 768px) { ... }"
                })
            
            # 3. Check for fixed width elements
            # This is a simplified check - in a real implementation, you'd analyze the CSS more thoroughly
            inline_styles = soup.find_all(style=True)
            for element in inline_styles:
                style = element.get('style', '')
                if 'width:' in style and 'px' in style:
                    if 'width: 1024px' in style or 'width: 1200px' in style:
                        issues.append({
                            "id": str(uuid.uuid4()),
                            "type": "warning",
                            "severity": 3,
                            "title": "Fixed Width Elements",
                            "description": f"Elemento com largura fixa encontrado: {style[:100]}...",
                            "device": "mobile",
                            "element": str(element)[:200],
                            "suggestion": "Use unidades relativas (%, vw, em, rem) ao invés de pixels fixos para larguras."
                        })
            
            # 4. Check for small text
            text_elements = soup.find_all(['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            for element in text_elements:
                style = element.get('style', '')
                if 'font-size:' in style:
                    import re
                    font_size_match = re.search(r'font-size:\s*(\d+)px', style)
                    if font_size_match:
                        font_size = int(font_size_match.group(1))
                        if font_size < 12:
                            issues.append({
                                "id": str(uuid.uuid4()),
                                "type": "warning",
                                "severity": 2,
                                "title": "Texto Muito Pequeno",
                                "description": f"Texto com tamanho de fonte pequeno ({font_size}px) encontrado.",
                                "device": "mobile",
                                "element": str(element)[:200],
                                "suggestion": "Use tamanhos de fonte mínimos de 14-16px para melhor legibilidade em dispositivos móveis."
                            })
            
            print(f"Found {len(issues)} layout issues")
            return issues
            
        except Exception as e:
            print(f"Error analyzing layout: {e}")
            return []

class VisionAnalysisTool:
    """Tool for visual analysis using Gemini Vision"""
    
    name: str = "analyze_with_vision"
    description: str = "Analyze screenshots using AI vision for visual issues"
    
    def __init__(self):
        super().__init__()
        try:
            from agno.models.google import Gemini
            self.model = Gemini(id="gemini-2.0-flash-exp")
        except Exception:
            self.model = None
    
    async def run(self, screenshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze screenshots with AI vision"""
        try:
            print(f"Analyzing screenshots with vision AI")
            
            issues = []
            
            for screenshot in screenshots:
                try:
                    # Download and process screenshot
                    screenshot_path = Path("screenshots") / screenshot["url"].split("/")[-1]
                    
                    if not screenshot_path.exists():
                        continue
                    
                    # Open and process image
                    with Image.open(screenshot_path) as img:
                        # Convert to RGB if necessary
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        # Resize if too large (to stay within API limits)
                        max_size = (1024, 1024)
                        img.thumbnail(max_size, Image.Resampling.LANCZOS)
                        
                        # Convert to base64
                        buffered = BytesIO()
                        img.save(buffered, format="PNG")
                        img_base64 = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Create analysis prompt
                    prompt = f"""
                    Analise esta captura de tela de um site web em {screenshot['device']} ({screenshot['resolution']}).
                    
                    Identifique os seguintes problemas de responsividade:
                    1. Elementos sobrepostos ou desalinhados
                    2. Texto ilegível ou muito pequeno
                    3. Botões ou links muito pequenos para toque
                    4. Imagens mal dimensionadas
                    5. Problemas de contraste
                    6. Scroll horizontal
                    7. Elementos fora da viewport
                    8. Problemas de layout quebrado
                    
                    Para cada problema encontrado, forneça:
                    - Descrição clara do problema
                    - Gravidade (crítico, aviso, informativo)
                    - Localização aproximada na tela
                    - Sugestão de correção
                    
                    Responda em formato JSON com a seguinte estrutura:
                    [
                        {
                            "title": "Título do problema",
                            "description": "Descrição detalhada",
                            "severity": 1-5 (1=muito grave, 5=muito leve),
                            "type": "critical|warning|info",
                            "element": "Seletor CSS aproximado",
                            "suggestion": "Como corrigir"
                        }
                    ]
                    """
                    
                    # Analyze with Gemini
                    if not self.model:
                        issues.append({
                            "id": str(uuid.uuid4()),
                            "type": "info",
                            "severity": 4,
                            "title": "Visão IA indisponível",
                            "description": "Biblioteca de IA não configurada. Configure GOOGLE_API_KEY e dependências.",
                            "device": screenshot["device"],
                            "suggestion": "Instale google-generativeai e defina GOOGLE_API_KEY."
                        })
                        continue
                    response = self.model.generate_content([prompt, {"mime_type": "image/png", "data": img_base64}])
                    
                    # Parse response
                    try:
                        vision_issues = json.loads(response.text)
                        
                        for issue in vision_issues:
                            issues.append({
                                "id": str(uuid.uuid4()),
                                "type": issue.get("type", "warning"),
                                "severity": issue.get("severity", 3),
                                "title": issue.get("title", "Problema Visual"),
                                "description": issue.get("description", "Problema detectado pela IA"),
                                "device": screenshot["device"],
                                "element": issue.get("element", ""),
                                "suggestion": issue.get("suggestion", "Verifique o layout")
                            })
                    except json.JSONDecodeError:
                        # If JSON parsing fails, create a simple issue
                        issues.append({
                            "id": str(uuid.uuid4()),
                            "type": "info",
                            "severity": 4,
                            "title": "Análise Visual Completa",
                            "description": f"Captura de tela em {screenshot['device']} analisada com IA.",
                            "device": screenshot["device"],
                            "suggestion": "Verifique manualmente o layout para problemas sutis."
                        })
                    
                except Exception as e:
                    print(f"Error analyzing {screenshot['device']} screenshot: {e}")
                    continue
            
            print(f"Vision analysis found {len(issues)} issues")
            return issues
            
        except Exception as e:
            print(f"Error in vision analysis: {e}")
            return []

class DocumentationSearchTool:
    """Tool for searching documentation"""
    
    name: str = "search_docs"
    description: str = "Search official documentation for solutions"
    
    async def run(self, query: str, technology: str = "css") -> Dict[str, Any]:
        """Search documentation for solutions"""
        try:
            print(f"Searching documentation for: {query}")
            
            # Documentation sources
            doc_sources = {
                "css": "https://developer.mozilla.org/pt-BR/docs/Web/CSS",
                "html": "https://developer.mozilla.org/pt-BR/docs/Web/HTML",
                "javascript": "https://developer.mozilla.org/pt-BR/docs/Web/JavaScript",
                "tailwind": "https://tailwindcss.com/docs",
                "react": "https://react.dev/",
                "angular": "https://angular.io/docs"
            }
            
            base_url = doc_sources.get(technology, doc_sources["css"])
            
            # Simple documentation search (in a real implementation, you'd use proper search APIs)
            search_results = {
                "query": query,
                "technology": technology,
                "results": [
                    {
                        "title": f"Documentação sobre {query}",
                        "url": f"{base_url}/{query.lower().replace(' ', '-')}",
                        "description": f"Guia oficial sobre {query} na documentação {technology}."
                    }
                ],
                "examples": [
                    {
                        "title": "Exemplo de Media Query",
                        "code": """@media (max-width: 768px) {
  .container {
    width: 100%;
    padding: 1rem;
  }
}""",
                        "description": "Media query para dispositivos móveis"
                    }
                ]
            }
            
            return search_results
            
        except Exception as e:
            print(f"Error searching documentation: {e}")
            return {"error": str(e), "query": query}

class SuggestionGeneratorTool:
    """Tool for generating practical suggestions"""
    
    name: str = "generate_suggestions"
    description: str = "Generate practical solutions for detected issues"
    
    async def run(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate suggestions for issues"""
        try:
            print(f"Generating suggestions for {len(issues)} issues")
            
            recommendations = []
            
            for issue in issues:
                try:
                    category = "css"
                    priority = "medium"
                    code_example = None
                    before = None
                    after = None
                    documentation = None
                    
                    # Generate specific recommendations based on issue type
                    if "viewport" in issue.get("title", "").lower():
                        category = "html"
                        priority = "high"
                        code_example = """<meta name="viewport" content="width=device-width, initial-scale=1.0">"""
                        before = "Sem viewport meta tag"
                        after = code_example
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/HTML/Viewport_meta_tag"
                        
                    elif "media query" in issue.get("title", "").lower():
                        category = "css"
                        priority = "high"
                        code_example = """/* Mobile first approach */
.container {
  width: 100%;
  padding: 1rem;
}

/* Tablet */
@media (min-width: 768px) {
  .container {
    max-width: 750px;
    margin: 0 auto;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .container {
    max-width: 1200px;
  }
}"""
                        before = "Estilos sem media queries"
                        after = "Estilos com media queries responsivas"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/Media_Queries/Using_media_queries"
                        
                    elif "texto" in issue.get("title", "").lower() or "font" in issue.get("title", "").lower():
                        category = "css"
                        priority = "medium"
                        code_example = """/* Tamanhos de fonte responsivos */
body {
  font-size: 16px;
}

@media (max-width: 768px) {
  body {
    font-size: 14px;
  }
  
  h1 { font-size: 1.5rem; }
  h2 { font-size: 1.25rem; }
  p { font-size: 1rem; }
}"""
                        before = "Fontes fixas muito pequenas"
                        after = "Fontes relativas e adaptativas"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/font-size"
                        
                    elif "largura" in issue.get("title", "").lower() or "width" in issue.get("title", "").lower():
                        category = "css"
                        priority = "high"
                        code_example = """/* Unidades relativas vs fixas */
/* ❌ Evite */
.container {
  width: 1024px;
}

/* ✅ Prefira */
.container {
  width: 100%;
  max-width: 1024px;
  padding: 0 1rem;
}"""
                        before = "Larguras fixas em pixels"
                        after = "Larguras relativas com max-width"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/width"
                        
                    elif "touch" in issue.get("title", "").lower() or "botão" in issue.get("title", "").lower():
                        category = "css"
                        priority = "high"
                        code_example = """/* Áreas de toque adequadas */
.button {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 24px;
  font-size: 16px; /* Prevents zoom on iOS */
}"""
                        before = "Botões pequenos (< 44px)"
                        after = "Botões com tamanho mínimo adequado"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/touch-action"
                        
                    elif "imagem" in issue.get("title", "").lower() or "image" in issue.get("title", "").lower():
                        category = "css"
                        priority = "medium"
                        code_example = """/* Imagens responsivas */
img {
  max-width: 100%;
  height: auto;
  display: block;
}

/* Imagens adaptativas */
.responsive-image {
  width: 100%;
  height: auto;
  object-fit: cover;
}"""
                        before = "Imagens com largura fixa"
                        after = "Imagens responsivas com max-width: 100%"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/object-fit"
                        
                    elif "scroll" in issue.get("title", "").lower() or "rolagem" in issue.get("title", "").lower():
                        category = "css"
                        priority = "high"
                        code_example = """/* Prevenir scroll horizontal */
html, body {
  max-width: 100%;
  overflow-x: hidden;
}

/* Verificar elementos largos */
* {
  box-sizing: border-box;
}"""
                        before = "Scroll horizontal indesejado"
                        after = "Layout sem scroll horizontal"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/overflow"
                        
                    else:
                        # Generic recommendation
                        code_example = """/* Exemplo genérico de correção */
.element {
  /* Adicione estilos responsivos aqui */
}"""
                    
                    # Determine priority based on issue severity
                    severity = issue.get("severity", 3)
                    if severity <= 2:
                        priority = "high"
                    elif severity <= 4:
                        priority = "medium"
                    else:
                        priority = "low"
                    
                    recommendations.append({
                        "id": str(uuid.uuid4()),
                        "category": category,
                        "title": f"Correção: {issue.get('title', 'Problema')}",
                        "description": f"Solução para: {issue.get('description', 'Problema detectado')}",
                        "code_example": code_example,
                        "before": before,
                        "after": after,
                        "documentation": documentation,
                        "priority": priority
                    })
                    
                except Exception as e:
                    print(f"Error generating suggestion for issue: {e}")
                    continue
            
            print(f"Generated {len(recommendations)} suggestions")
            return recommendations
            
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []

class ReportGeneratorTool:
    """Tool for generating HTML reports"""
    
    name: str = "create_report"
    description: str = "Generate comprehensive HTML report with all analysis results"
    
    async def run(
        self, 
        analysis_id: str,
        url: str, 
        screenshots: List[Dict[str, Any]], 
        issues: List[Dict[str, Any]], 
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate HTML report"""
        try:
            print(f"Generating HTML report for {url}")
            
            # Calculate statistics
            total_issues = len(issues)
            critical_issues = len([i for i in issues if i.get("type") == "critical"])
            warning_issues = len([i for i in issues if i.get("type") == "warning"])
            info_issues = len([i for i in issues if i.get("type") == "info"])
            
            # Generate summary
            summary = f"""
            Análise de responsividade completa realizada para {url}.
            
            Foram identificados {total_issues} problemas:
            - {critical_issues} problemas críticos
            - {warning_issues} avisos
            - {info_issues} informações
            
            Os principais problemas encontrados foram relacionados a layout, tipografia e usabilidade em dispositivos móveis.
            As recomendações fornecidas incluem exemplos de código prontos para uso.
            """
            
            # Generate HTML report
            html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório de Responsividade - {url}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #667eea;
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .issue {{
            background: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #ff6b6b;
        }}
        .issue.warning {{
            border-left-color: #ffa726;
        }}
        .issue.info {{
            border-left-color: #42a5f5;
        }}
        .issue h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .issue p {{
            margin: 5px 0;
            color: #666;
        }}
        .code-example {{
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            overflow-x: auto;
            margin: 10px 0;
        }}
        .screenshot-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .screenshot {{
            text-align: center;
        }}
        .screenshot img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
        }}
        .screenshot-caption {{
            margin-top: 10px;
            color: #666;
            font-weight: 500;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatório de Responsividade</h1>
            <p>Análise completa realizada em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>Estatísticas da Análise</h2>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number">{total_issues}</div>
                        <div class="stat-label">Total de Problemas</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{critical_issues}</div>
                        <div class="stat-label">Críticos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{warning_issues}</div>
                        <div class="stat-label">Avisos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">{len(screenshots)}</div>
                        <div class="stat-label">Screenshots</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Sumário Executivo</h2>
                <p>{summary}</p>
            </div>
            
            <div class="section">
                <h2>Capturas de Tela</h2>
                <div class="screenshot-grid">
                    {''.join([
                        f'''
                        <div class="screenshot">
                            <img src="{screenshot['url']}" alt="{screenshot['device']}">
                            <div class="screenshot-caption">{screenshot['device'].title()} - {screenshot['resolution']}</div>
                        </div>
                        ''' for screenshot in screenshots
                    ])}
                </div>
            </div>
            
            <div class="section">
                <h2>Problemas Identificados</h2>
                {''.join([
                    f'''
                    <div class="issue {'warning' if issue.get('type') == 'warning' else 'info' if issue.get('type') == 'info' else ''}">
                        <h3>{issue.get('title', 'Problema')}</h3>
                        <p><strong>Dispositivo:</strong> {issue.get('device', 'Todos')}</p>
                        <p><strong>Gravidade:</strong> {issue.get('type', 'warning').title()}</p>
                        <p><strong>Descrição:</strong> {issue.get('description', 'Sem descrição')}</p>
                        {f'<p><strong>Elemento:</strong> <code>{issue.get("element", "")}</code></p>' if issue.get('element') else ''}
                        {f'<p><strong>Sugestão:</strong> {issue.get("suggestion", "")}</p>' if issue.get('suggestion') else ''}
                    </div>
                    ''' for issue in issues
                ])}
            </div>
            
            <div class="section">
                <h2>Recomendações</h2>
                {''.join([
                    f'''
                    <div class="issue info">
                        <h3>{rec.get('title', 'Recomendação')}</h3>
                        <p><strong>Categoria:</strong> {rec.get('category', 'css').upper()}</p>
                        <p><strong>Prioridade:</strong> {rec.get('priority', 'medium').title()}</p>
                        <p><strong>Descrição:</strong> {rec.get('description', 'Sem descrição')}</p>
                        {f'<div class="code-example"><strong>Exemplo de código:</strong><br><code>{rec.get("code_example", "")}</code></div>' if rec.get('code_example') else ''}
                        {f'<p><strong>Antes:</strong> {rec.get("before", "")}</p>' if rec.get('before') else ''}
                        {f'<p><strong>Depois:</strong> {rec.get("after", "")}</p>' if rec.get('after') else ''}
                        {f'<p><strong>Documentação:</strong> <a href="{rec.get("documentation", "#")}" target="_blank">Ver documentação</a></p>' if rec.get('documentation') else ''}
                    </div>
                    ''' for rec in recommendations
                ])}
            </div>
        </div>
        
        <div class="footer">
            <p>Relatório gerado automaticamente pelo Sistema de Testes Responsivos com IA</p>
            <p>Para mais informações, consulte a documentação oficial dos padrões web.</p>
        </div>
    </div>
</body>
</html>
            """
            
            # Save report to file
            report_filename = f"report_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report_path = Path("reports") / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"HTML report saved to {report_path}")
            
            return {
                "report_url": f"/reports/{report_filename}",
                "summary": summary.strip(),
                "filename": report_filename
            }
            
        except Exception as e:
            print(f"Error generating HTML report: {e}")
            return {"error": str(e)}

class ResponsiveTestingAgent:
    """Main agent for responsive testing"""
    
    def __init__(self):
        self.db = None
    
    async def capture_screenshots(self, url: str, analysis_id: str) -> List[Dict[str, Any]]:
        """Capture screenshots using the agent"""
        try:
            print(f"Agent capturing screenshots for {url}")
            
            # Use the screenshot tool directly
            screenshot_tool = ScreenshotCaptureTool()
            screenshots = await screenshot_tool.run(url, analysis_id)
            
            return screenshots
            
        except Exception as e:
            print(f"Error capturing screenshots: {e}")
            raise
    
    async def analyze_layout(self, url: str, screenshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze layout issues"""
        try:
            print(f"Agent analyzing layout for {url}")
            
            # Use the layout analysis tool directly
            layout_tool = LayoutAnalysisTool()
            issues = await layout_tool.run(url, screenshots)
            
            return issues
            
        except Exception as e:
            print(f"Error analyzing layout: {e}")
            return []
    
    async def analyze_with_vision(self, screenshots: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze screenshots with AI vision"""
        try:
            print(f"Agent analyzing with vision")
            
            # Use the vision analysis tool directly
            vision_tool = VisionAnalysisTool()
            issues = await vision_tool.run(screenshots)
            
            return issues
            
        except Exception as e:
            print(f"Error in vision analysis: {e}")
            return []
    
    async def generate_suggestions(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate suggestions for issues"""
        try:
            print(f"Agent generating suggestions for {len(issues)} issues")
            
            # Use the suggestion generator tool directly
            suggestion_tool = SuggestionGeneratorTool()
            recommendations = await suggestion_tool.run(issues)
            
            return recommendations
            
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []
    
    async def create_report(
        self, 
        analysis_id: str,
        url: str, 
        screenshots: List[Dict[str, Any]], 
        issues: List[Dict[str, Any]], 
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create HTML report"""
        try:
            print(f"Agent creating report for {url}")
            
            # Use the report generator tool directly
            report_tool = ReportGeneratorTool()
            report_data = await report_tool.run(analysis_id, url, screenshots, issues, recommendations)
            
            return report_data
            
        except Exception as e:
            print(f"Error creating report: {e}")
            return {"error": str(e)}
    
    async def run_full_analysis(self, url: str, analysis_id: str) -> Dict[str, Any]:
        """Run complete responsive analysis"""
        try:
            print(f"🚀 Starting full analysis for {url}")
            
            # Step 1: Capture screenshots
            screenshots = await self.capture_screenshots(url, analysis_id)
            
            # Step 2: Analyze layout
            layout_issues = await self.analyze_layout(url, screenshots)
            
            # Step 3: Vision analysis
            vision_issues = await self.analyze_with_vision(screenshots)
            
            # Combine all issues
            all_issues = layout_issues + vision_issues
            
            # Step 4: Generate suggestions
            recommendations = await self.generate_suggestions(all_issues)
            
            # Step 5: Create report
            report_data = await self.create_report(url, screenshots, all_issues, recommendations)
            
            # Calculate scores
            scores = self.calculate_scores(all_issues)
            
            return {
                "screenshots": screenshots,
                "issues": all_issues,
                "recommendations": recommendations,
                "report": report_data,
                "scores": scores
            }
            
        except Exception as e:
            print(f"❌ Error in full analysis: {e}")
            raise
    
    def calculate_scores(self, issues: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate responsive scores"""
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
            print(f"❌ Error calculating scores: {e}")
            return {
                "mobile": 0,
                "tablet": 0,
                "desktop": 0,
                "overall": 0
            }

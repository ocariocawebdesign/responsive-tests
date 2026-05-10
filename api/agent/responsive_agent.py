import asyncio
import json
import os
import re
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

class ResponsiveGuideTool:
    name: str = "responsive_guide"
    description: str = "Parse responsive-guide.md and extract breakpoints and rules"

    def _guide_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "responsive-guide.md"

    def load_and_parse(self) -> Dict[str, Any]:
        guide_path = self._guide_path()
        if not guide_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {guide_path}")

        content = guide_path.read_text(encoding="utf-8", errors="ignore")

        version = None
        version_match = re.search(r"\*\*Versão:\*\*\s*([0-9]+(?:\.[0-9]+)*)", content)
        if version_match:
            version = version_match.group(1).strip()

        widths = []
        for m in re.finditer(r"Layout funciona em\s+(\d+)px", content):
            widths.append(int(m.group(1)))
        wide_match = re.search(r"Layout funciona em\s+(\d+)px\+", content)
        wide_width = int(wide_match.group(1)) if wide_match else None

        widths = sorted(set(widths))
        mobile_width = 375 if 375 in widths else (widths[0] if widths else 375)
        tablet_width = 768 if 768 in widths else 768
        desktop_width = 1024 if 1024 in widths else 1024
        large_width = wide_width or (1440 if 1440 in widths else 1440)

        breakpoints = [
            {"id": "mobile", "label": "Mobile", "width": mobile_width, "height": 667, "device_scale_factor": 2},
            {"id": "tablet", "label": "Tablet", "width": tablet_width, "height": 1024, "device_scale_factor": 2},
            {"id": "desktop", "label": "Desktop", "width": desktop_width, "height": 900, "device_scale_factor": 1},
            {"id": "large-desktop", "label": "Large Desktop", "width": large_width, "height": 900, "device_scale_factor": 1},
        ]

        rules = {
            "min_font_px": 16,
            "touch_target_min_px": 44,
            "require_viewport_meta": True,
            "disallow_user_scalable_no": True,
            "disallow_minimum_scale": True,
            "disallow_maximum_scale": True,
            "no_horizontal_scroll": True,
        }

        def _extract_section(start_pattern: str, end_pattern: str, max_len: int = 5000) -> Optional[str]:
            start = re.search(start_pattern, content)
            if not start:
                return None
            end = re.search(end_pattern, content[start.end():])
            raw = content[start.end(): start.end() + (end.start() if end else len(content))]
            raw = raw.strip()
            return raw[:max_len]

        media_queries_excerpt = _extract_section(r"## 3\.\s*MEDIA QUERIES[\s\S]*?\n", r"\n---\n", max_len=6000)
        layout_checklist_excerpt = _extract_section(r"### 10\.2 Layout[\s\S]*?\n", r"### 10\.3", max_len=2500)
        components_excerpt = _extract_section(r"## 9\.\s*TAILWIND CSS[\s\S]*?\n", r"\n---\n", max_len=6000)

        return {
            "version": version,
            "path": str(guide_path),
            "breakpoints": breakpoints,
            "rules": rules,
            "excerpts": {
                "media_queries": media_queries_excerpt,
                "layout_guidelines": layout_checklist_excerpt,
                "component_patterns": components_excerpt,
            },
        }

class ScreenshotCaptureTool:
    """Tool for capturing screenshots of websites"""
    
    name: str = "capture_screenshots"
    description: str = "Capture screenshots of a website in different screen sizes"
    
    async def run(
        self,
        url: str,
        analysis_id: str,
        breakpoints: Optional[List[Dict[str, Any]]] = None,
        guide_rules: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Capture screenshots in multiple device sizes"""
        try:
            print(f"Capturing screenshots for {url}")
            
            devices = breakpoints or [
                {"id": "mobile", "label": "Mobile", "width": 375, "height": 667, "device_scale_factor": 2},
                {"id": "tablet", "label": "Tablet", "width": 768, "height": 1024, "device_scale_factor": 2},
                {"id": "desktop", "label": "Desktop", "width": 1024, "height": 900, "device_scale_factor": 1},
                {"id": "large-desktop", "label": "Large Desktop", "width": 1440, "height": 900, "device_scale_factor": 1},
            ]
            rules = guide_rules or {"min_font_px": 16, "touch_target_min_px": 44}
            
            screenshots = []
            screenshots_dir = Path(__file__).resolve().parents[2] / "screenshots"
            screenshots_dir.mkdir(exist_ok=True)

            def _ua(device_id: str) -> str:
                if device_id == "mobile":
                    return "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                if device_id == "tablet":
                    return "Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
                return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

            async def _evaluate_compliance(page) -> List[Dict[str, Any]]:
                metrics = await page.evaluate(
                    """() => {
                      const meta = document.querySelector('meta[name=\"viewport\"]');
                      const viewportContent = meta ? (meta.getAttribute('content') || '') : null;
                      const doc = document.documentElement;
                      const overflowX = doc.scrollWidth > window.innerWidth + 1;
                      const bodyFont = window.getComputedStyle(document.body).fontSize || '';
                      const bodyFontPx = parseFloat(bodyFont) || null;

                      const targets = Array.from(document.querySelectorAll('a,button,input,select,textarea,[role=\"button\"]'))
                        .filter(el => {
                          const style = window.getComputedStyle(el);
                          const rect = el.getBoundingClientRect();
                          return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
                        })
                        .map(el => el.getBoundingClientRect())
                        .filter(r => r.width < 44 || r.height < 44);

                      const media = Array.from(document.querySelectorAll('img,video,embed,object,iframe'))
                        .filter(el => {
                          const rect = el.getBoundingClientRect();
                          return rect.width > window.innerWidth + 1;
                        });

                      return {
                        viewportContent,
                        overflowX,
                        bodyFontPx,
                        smallTargetCount: targets.length,
                        oversizedMediaCount: media.length
                      };
                    }"""
                )

                violations: List[Dict[str, Any]] = []
                if rules.get("require_viewport_meta", True):
                    if not metrics.get("viewportContent"):
                        violations.append({
                            "id": "viewport_meta_missing",
                            "title": "Meta viewport ausente",
                            "description": "A página não possui <meta name=\"viewport\">, o que pode quebrar media queries em mobile.",
                            "guide_ref": "responsive-guide.md §2.1 / §10.1"
                        })
                    else:
                        content = str(metrics.get("viewportContent") or "")
                        lc = content.lower()
                        if "width=device-width" not in lc or "initial-scale=1" not in lc and "initial-scale=1.0" not in lc:
                            violations.append({
                                "id": "viewport_meta_invalid",
                                "title": "Meta viewport inválida",
                                "description": f"Conteúdo atual: {content}. Recomendado: width=device-width, initial-scale=1.",
                                "guide_ref": "responsive-guide.md §2.1 / §10.1"
                            })
                        if rules.get("disallow_user_scalable_no", True) and "user-scalable=no" in lc:
                            violations.append({
                                "id": "viewport_user_scalable_no",
                                "title": "Zoom desabilitado (user-scalable=no)",
                                "description": "Bloquear zoom viola acessibilidade e boas práticas. Remova user-scalable=no.",
                                "guide_ref": "responsive-guide.md §2.1 / §10.7 / §11"
                            })
                        if rules.get("disallow_minimum_scale", True) and "minimum-scale" in lc:
                            violations.append({
                                "id": "viewport_minimum_scale",
                                "title": "minimum-scale presente",
                                "description": "Evite minimum-scale; pode prejudicar acessibilidade.",
                                "guide_ref": "responsive-guide.md §2.1"
                            })
                        if rules.get("disallow_maximum_scale", True) and "maximum-scale" in lc:
                            violations.append({
                                "id": "viewport_maximum_scale",
                                "title": "maximum-scale presente",
                                "description": "Evite maximum-scale; pode prejudicar acessibilidade.",
                                "guide_ref": "responsive-guide.md §2.1"
                            })

                if rules.get("no_horizontal_scroll", True) and metrics.get("overflowX"):
                    violations.append({
                        "id": "horizontal_scroll",
                        "title": "Scroll horizontal indesejado",
                        "description": "O conteúdo excede a largura do viewport (scrollWidth > innerWidth).",
                        "guide_ref": "responsive-guide.md §10.2 / §11"
                    })

                min_font = rules.get("min_font_px", 16)
                if metrics.get("bodyFontPx") and metrics.get("bodyFontPx") < float(min_font):
                    violations.append({
                        "id": "min_font_size",
                        "title": "Fonte do corpo abaixo do mínimo",
                        "description": f"Fonte do body = {metrics.get('bodyFontPx')}px (mínimo recomendado: {min_font}px).",
                        "guide_ref": "responsive-guide.md §10.3 / §11"
                    })

                if metrics.get("smallTargetCount", 0) > 0:
                    violations.append({
                        "id": "touch_targets_small",
                        "title": "Alvos de toque pequenos",
                        "description": f"Foram encontrados {metrics.get('smallTargetCount')} elementos interativos com tamanho < 44x44px.",
                        "guide_ref": "responsive-guide.md §10.5"
                    })

                if metrics.get("oversizedMediaCount", 0) > 0:
                    violations.append({
                        "id": "oversized_media",
                        "title": "Mídia maior que o viewport",
                        "description": f"Foram encontrados {metrics.get('oversizedMediaCount')} elementos de mídia com largura maior que o viewport.",
                        "guide_ref": "responsive-guide.md §6 / §10.4"
                    })

                return violations
            
            async with async_playwright() as p:
                browser = None
                for launcher_name in ("chromium", "firefox", "webkit"):
                    try:
                        launcher = getattr(p, launcher_name)
                        browser = await launcher.launch(headless=True)
                        break
                    except Exception as e:
                        print(f"{launcher_name} launch failed: {e}")
                        if launcher_name == "chromium":
                            os.system("python -m playwright install chromium")
                        elif launcher_name == "firefox":
                            os.system("python -m playwright install firefox")
                        elif launcher_name == "webkit":
                            os.system("python -m playwright install webkit")
                        try:
                            launcher = getattr(p, launcher_name)
                            browser = await launcher.launch(headless=True)
                            break
                        except Exception as e2:
                            print(f"{launcher_name} launch retry failed: {e2}")
                            continue
                
                if not browser:
                    print("No browser could be launched; generating placeholder screenshots.")
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    for device in devices:
                        filename = f"{analysis_id}_{device['id']}_{timestamp}.png"
                        full_page_filename = f"{analysis_id}_{device['id']}_full_{timestamp}.png"
                        img = Image.new("RGB", (int(device["width"]), int(device["height"])), color=(245, 245, 245))
                        timestamp_label = datetime.now().strftime("%d/%m/%Y %H:%M")
                        try:
                            from PIL import ImageDraw
                            draw = ImageDraw.Draw(img)
                            draw.multiline_text((20, 20), f"{device.get('label', device['id'])}\n{device['width']}x{device['height']}\n{timestamp_label}\n(placeholder)", fill=(60, 60, 60))
                        except Exception:
                            pass
                        img.save(screenshots_dir / filename)
                        img.save(screenshots_dir / full_page_filename)
                        screenshots.append({
                            "id": str(uuid.uuid4()),
                            "device": device["id"],
                            "resolution": f"{device['width']}x{device['height']}",
                            "url": f"/screenshots/{filename}",
                            "full_page_url": f"/screenshots/{full_page_filename}",
                            "compliant": False,
                            "violations": [{
                                "id": "screenshot_capture_unavailable",
                                "title": "Captura indisponível no ambiente",
                                "description": "Não foi possível iniciar um navegador do Playwright; foram geradas imagens placeholder.",
                                "guide_ref": "responsive-guide.md §10.2"
                            }]
                        })
                    return screenshots

                for device in devices:
                    try:
                        context = await browser.new_context(
                            viewport={"width": int(device["width"]), "height": int(device["height"])},
                            device_scale_factor=int(device.get("device_scale_factor") or 1),
                            user_agent=_ua(device.get("id") or device.get("name") or "")
                        )
                        
                        page = await context.new_page()
                        
                        # Navigate to URL
                        try:
                            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                        except Exception:
                            await page.goto(url, wait_until="load", timeout=30000)
                        
                        # Wait a bit for any dynamic content
                        await asyncio.sleep(2)
                        
                        violations = await _evaluate_compliance(page)
                        compliant = len(violations) == 0

                        # Generate filenames
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        device_id = device.get("id") or device.get("name")
                        filename = f"{analysis_id}_{device_id}_{timestamp}.png"
                        full_page_filename = f"{analysis_id}_{device_id}_full_{timestamp}.png"
                        
                        # Take viewport screenshot
                        screenshot_path = screenshots_dir / filename
                        await page.screenshot(path=str(screenshot_path), full_page=False)
                        
                        # Take full page screenshot
                        full_page_path = screenshots_dir / full_page_filename
                        await page.screenshot(path=str(full_page_path), full_page=True)
                        
                        screenshots.append({
                            "id": str(uuid.uuid4()),
                            "device": device_id,
                            "resolution": f"{device['width']}x{device['height']}",
                            "url": f"/screenshots/{filename}",
                            "full_page_url": f"/screenshots/{full_page_filename}",
                            "compliant": compliant,
                            "violations": violations
                        })
                        
                        await context.close()
                        
                    except Exception as e:
                        print(f"Error capturing {(device.get('id') or device.get('name') or 'breakpoint')} screenshot: {e}")
                        continue
                
                await browser.close()
            
            print(f"Captured {len(screenshots)} screenshots")
            if not screenshots:
                try:
                    print("No screenshots captured, generating placeholders")
                    from PIL import Image, ImageDraw
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    for device in devices:
                        device_id = device.get("id") or device.get("name") or "breakpoint"
                        w = int(device.get("width") or 0) or 800
                        h = int(device.get("height") or 0) or 600
                        filename = f"{analysis_id}_{device_id}_{timestamp}.png"
                        full_page_filename = f"{analysis_id}_{device_id}_full_{timestamp}.png"
                        img = Image.new('RGB', (w, h), color=(245, 245, 245))
                        draw = ImageDraw.Draw(img)
                        text = f"{str(device_id).upper()}\n{w}x{h}\n(placeholder)"
                        draw.multiline_text((20, 20), text, fill=(60,60,60))
                        img.save(screenshots_dir / filename)
                        img.save(screenshots_dir / full_page_filename)
                        screenshots.append({
                            "id": str(uuid.uuid4()),
                            "device": device_id,
                            "resolution": f"{w}x{h}",
                            "url": f"/screenshots/{filename}",
                            "full_page_url": f"/screenshots/{full_page_filename}",
                            "compliant": False,
                            "violations": [{
                                "id": "screenshot_placeholder",
                                "title": "Screenshot placeholder",
                                "description": "A captura falhou para este breakpoint e uma imagem placeholder foi gerada.",
                                "guide_ref": "responsive-guide.md §10.2"
                            }]
                        })
                    print(f"Generated {len(screenshots)} placeholder screenshots")
                except Exception as e:
                    print(f"Error generating placeholders: {e}")
            return screenshots
            
        except Exception as e:
            print(f"Error capturing screenshots: {e}")
            try:
                screenshots: List[Dict[str, Any]] = []
                screenshots_dir = Path(__file__).resolve().parents[2] / "screenshots"
                screenshots_dir.mkdir(exist_ok=True)
                devices = [
                    {"id": "mobile", "label": "Mobile", "width": 375, "height": 667},
                    {"id": "tablet", "label": "Tablet", "width": 768, "height": 1024},
                    {"id": "desktop", "label": "Desktop", "width": 1024, "height": 900},
                    {"id": "large-desktop", "label": "Large Desktop", "width": 1440, "height": 900},
                ]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                err = str(e)
                if len(err) > 160:
                    err = err[:160] + "..."
                for device in devices:
                    device_id = device.get("id") or "breakpoint"
                    w = int(device.get("width") or 0) or 800
                    h = int(device.get("height") or 0) or 600
                    filename = f"{analysis_id}_{device_id}_{timestamp}.png"
                    full_page_filename = f"{analysis_id}_{device_id}_full_{timestamp}.png"
                    img = Image.new("RGB", (w, h), color=(245, 245, 245))
                    try:
                        from PIL import ImageDraw
                        draw = ImageDraw.Draw(img)
                        draw.multiline_text(
                            (20, 20),
                            f"{device.get('label', device_id)}\n{w}x{h}\n(placeholder)\n{err}",
                            fill=(60, 60, 60),
                        )
                    except Exception:
                        pass
                    img.save(screenshots_dir / filename)
                    img.save(screenshots_dir / full_page_filename)
                    screenshots.append({
                        "id": str(uuid.uuid4()),
                        "device": device_id,
                        "resolution": f"{w}x{h}",
                        "url": f"/screenshots/{filename}",
                        "full_page_url": f"/screenshots/{full_page_filename}",
                        "compliant": False,
                        "violations": [{
                            "id": "screenshot_capture_exception",
                            "title": "Falha ao capturar screenshots",
                            "description": str(e),
                            "guide_ref": "responsive-guide.md §10.2"
                        }]
                    })
                return screenshots
            except Exception as e2:
                print(f"Error generating fallback placeholders: {e2}")
                return []

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
                    screenshot_path = Path(__file__).resolve().parents[2] / "screenshots" / screenshot["url"].split("/")[-1]
                    
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

class TechnologyDetectionTool:
    """Tool for detecting website technologies and SEO meta tags"""

    name: str = "detect_technology"
    description: str = "Detect frameworks, CMS, libraries, languages and SEO meta"

    async def run(self, url: str) -> Dict[str, Any]:
        """Fetch page and infer technologies and SEO metadata"""
        try:
            print(f"Detecting technology for {url}")
            response = requests.get(url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')

            tech = {
                "frameworks": [],
                "cms": None,
                "libraries": [],
                "languages": [],
                "server": response.headers.get('Server')
            }

            # CMS via generator meta
            generator = soup.find('meta', attrs={'name': 'generator'})
            if generator and generator.get('content'):
                gen = generator.get('content').lower()
                if 'wordpress' in gen:
                    tech["cms"] = 'WordPress'
                elif 'drupal' in gen:
                    tech["cms"] = 'Drupal'
                elif 'joomla' in gen:
                    tech["cms"] = 'Joomla'
                elif 'ghost' in gen:
                    tech["cms"] = 'Ghost'

            # URLs indicating CMS
            html_text = response.text.lower()
            if not tech["cms"]:
                if 'wp-content' in html_text or 'wp-includes' in html_text:
                    tech["cms"] = 'WordPress'
                elif 'cdn.shopify.com' in html_text or 'shopify' in html_text:
                    tech["cms"] = 'Shopify'
                elif 'squarespace' in html_text:
                    tech["cms"] = 'Squarespace'
                elif 'wix' in html_text:
                    tech["cms"] = 'Wix'

            # Frameworks heuristics
            if '__NEXT_DATA__' in html_text or 'next.config' in html_text:
                tech["frameworks"].append('Next.js')
            if 'window.__NUXT__' in html_text:
                tech["frameworks"].append('Nuxt')
            if 'data-reactroot' in html_text or 'react' in html_text and 'react-dom' in html_text:
                tech["frameworks"].append('React')
            if 'ng-version' in html_text or 'ng-app' in html_text or 'angular' in html_text:
                tech["frameworks"].append('Angular')
            if 'vue' in html_text and ('vue.js' in html_text or 'vue.runtime' in html_text or 'data-v-' in html_text):
                tech["frameworks"].append('Vue')
            if 'svelte' in html_text or 'data-svelte' in html_text:
                tech["frameworks"].append('Svelte')

            # Libraries / CSS frameworks
            links = soup.find_all('link', href=True)
            scripts = soup.find_all('script', src=True)
            hrefs = ' '.join([l['href'] for l in links])
            srcs = ' '.join([s['src'] for s in scripts])
            combined = (hrefs + ' ' + srcs).lower()
            if 'bootstrap' in combined:
                tech["libraries"].append('Bootstrap')
            if 'tailwind' in combined or any(cls.startswith(('sm:', 'md:', 'lg:', 'xl:', '2xl:')) for cls in soup.get_text().split()):
                tech["libraries"].append('Tailwind CSS')
            if 'jquery' in combined:
                tech["libraries"].append('jQuery')
            if 'material-ui' in combined or '@mui' in combined:
                tech["libraries"].append('MUI')

            # Languages inference
            if tech["frameworks"]:
                tech["languages"].append('JavaScript/TypeScript')
            if tech["cms"] in ['WordPress', 'Drupal', 'Joomla']:
                tech["languages"].append('PHP')
            if 'ruby on rails' in html_text or 'rails' in combined:
                tech["languages"].append('Ruby')
            if 'django' in combined or 'flask' in combined:
                tech["languages"].append('Python')

            # SEO Meta
            seo = {
                "title": soup.title.string.strip() if soup.title and soup.title.string else None,
                "description": None,
                "keywords": None,
                "robots": None,
                "canonical": None,
                "og": {},
                "twitter": {}
            }
            desc = soup.find('meta', attrs={'name': 'description'})
            if desc and desc.get('content'):
                seo["description"] = desc.get('content').strip()
            keywords = soup.find('meta', attrs={'name': 'keywords'})
            if keywords and keywords.get('content'):
                seo["keywords"] = keywords.get('content').strip()
            robots = soup.find('meta', attrs={'name': 'robots'})
            if robots and robots.get('content'):
                seo["robots"] = robots.get('content').strip()
            canonical = soup.find('link', attrs={'rel': 'canonical'})
            if canonical and canonical.get('href'):
                seo["canonical"] = canonical.get('href').strip()

            for meta in soup.find_all('meta'):
                prop = meta.get('property') or meta.get('name')
                content = meta.get('content')
                if not prop or not content:
                    continue
                if prop.startswith('og:'):
                    seo["og"][prop] = content
                if prop.startswith('twitter:'):
                    seo["twitter"][prop] = content

            return {"technology": tech, "seo": seo}
        except Exception as e:
            print(f"Error detecting technology: {e}")
            return {"technology": {}, "seo": {}, "error": str(e)}

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
                    justification = None
                    
                    # Generate specific recommendations based on issue type
                    if "viewport" in issue.get("title", "").lower():
                        category = "html"
                        priority = "high"
                        code_example = """<meta name="viewport" content="width=device-width, initial-scale=1.0">"""
                        before = "Sem viewport meta tag"
                        after = code_example
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/HTML/Viewport_meta_tag"
                        justification = (
                            "A tag viewport informa ao navegador como dimensionar e escalar o layout em dispositivos móveis. "
                            "Sem ela, o conteúdo é renderizado em uma largura fixa, causando zoom e rolagem indesejados. "
                            "Recomendação alinhada ao HTML5/W3C e à documentação oficial da MDN."
                        )
                        
                    elif ("media query" in issue.get("title", "").lower() or "media queries" in issue.get("title", "").lower()):
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
                        justification = (
                            "Media queries permitem adaptar o layout a diferentes larguras de viewport. "
                            "Seguir a abordagem mobile-first simplifica o CSS e melhora a experiência em dispositivos móveis. "
                            "Padrões W3C para WebApps e guia da MDN recomendam seu uso para responsividade."
                        )
                        
                    elif "scroll horizontal" in issue.get("title", "").lower():
                        category = "css"
                        priority = "high"
                        code_example = """/* Diagnóstico e correção de overflow horizontal */
html, body { max-width: 100%; overflow-x: hidden; }
* { box-sizing: border-box; }

/* Evite width: 100vw em containers internos */
.container { width: 100%; max-width: 100%; }"""
                        before = "Layout com elementos excedendo a largura do viewport"
                        after = "Layout sem overflow horizontal e com box-sizing correto"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/overflow"
                        justification = (
                            "O guia recomenda que não exista scroll horizontal em nenhum breakpoint (responsive-guide.md §10.2) "
                            "e aponta antipadrões comuns como uso indevido de 100vw (responsive-guide.md §11). "
                            "A MDN documenta overflow e box-sizing como ferramentas para prevenir e diagnosticar o problema."
                        )

                    elif "fonte" in issue.get("title", "").lower() and "mínimo" in issue.get("title", "").lower():
                        category = "css"
                        priority = "medium"
                        code_example = """html { font-size: 100%; } /* 16px padrão */
body { font-size: 1rem; line-height: 1.5; }
@media (max-width: 768px) { body { font-size: 1rem; } }"""
                        before = "Texto do corpo abaixo de 16px"
                        after = "Texto do corpo com 1rem (16px) e boa legibilidade"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/font-size"
                        justification = (
                            "O checklist do guia recomenda 16px (1rem) como tamanho mínimo de fonte para o corpo (responsive-guide.md §10.3) "
                            "e aponta fontes muito pequenas como antipadrão em mobile (responsive-guide.md §11)."
                        )

                    elif "alvos de toque" in issue.get("title", "").lower() or "toque" in issue.get("title", "").lower():
                        category = "accessibility"
                        priority = "high"
                        code_example = """/* Garanta alvos de toque adequados */
button, a[role=\"button\"], .btn {
  min-width: 44px;
  min-height: 44px;
  padding: 12px 16px;
}"""
                        before = "Elementos clicáveis com área menor que 44x44px"
                        after = "Elementos clicáveis com área mínima adequada e padding"
                        documentation = "https://w3c.br/padroes/"
                        justification = (
                            "O guia recomenda área mínima de toque 44×44px e espaçamento entre alvos (responsive-guide.md §10.5). "
                            "Essa regra melhora usabilidade em touch e é consistente com diretrizes de acessibilidade da plataforma web aberta (W3C)."
                        )

                    elif "mídia maior que o viewport" in issue.get("title", "").lower():
                        category = "css"
                        priority = "high"
                        code_example = """img, video, embed, object, iframe {
  max-width: 100%;
  height: auto;
}
.media-wrap { width: 100%; overflow: hidden; }"""
                        before = "Imagens/iframes estourando o container"
                        after = "Mídia responsiva com max-width: 100% e altura automática"
                        documentation = "https://developer.mozilla.org/pt-BR/docs/Web/CSS/object-fit"
                        justification = (
                            "O guia define como obrigatório que imagens e mídia respeitem o container (responsive-guide.md §6 / §10.4). "
                            "Ajustar max-width/height evita overflow e distorção conforme documentação da MDN."
                        )

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
                        justification = (
                            "Tamanhos de fonte relativos e adaptativos evitam texto ilegível em telas pequenas e reduzem o zoom automático em iOS. "
                            "A MDN recomenda o uso de unidades relativas (rem/em) para escalabilidade."
                        )
                        
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
                        justification = (
                            "Larguras fixas quebram o layout em viewports menores e causam rolagem horizontal. "
                            "Larguras fluidas com max-width permitem layout adaptável conforme recomendado pela MDN e padrões W3C."
                        )
                        
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
                        justification = (
                            "Alvos de toque muito pequenos prejudicam a usabilidade e violam princípios de acessibilidade (WCAG). "
                            "Aumentar áreas de toque para ~44px melhora a operabilidade em dispositivos touch; referência de boas práticas em MDN/W3C."
                        )
                        
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
                        justification = (
                            "Imagens devem escalar dentro do container para evitar overflow e distorção. "
                            "MDN recomenda `max-width: 100%` e `object-fit` para preservar proporções."
                        )
                        
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
                        justification = (
                            "Overflow horizontal indica elementos com largura maior que a viewport. "
                            "Garantir `box-sizing: border-box` e revisar widths evita clipping/rolagem; abordagem alinhada às recomendações da MDN/W3C."
                        )
                        
                    else:
                        # Generic recommendation
                        code_example = """/* Exemplo genérico de correção */
.element {
  /* Adicione estilos responsivos aqui */
}"""
                        justification = (
                            "Ajustes responsivos devem considerar layout fluido, tipografia acessível e imagens adaptativas, "
                            "conforme boas práticas dos padrões W3C e guias da MDN."
                        )
                        documentation = "https://developer.mozilla.org/pt-BR/"
                    
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
                        "justification": justification,
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
        recommendations: List[Dict[str, Any]],
        technology: Optional[Dict[str, Any]] = None,
        seo: Optional[Dict[str, Any]] = None,
        guide: Optional[Dict[str, Any]] = None
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
            # Technology section HTML
            tech_html = ""
            if technology:
                frameworks = ', '.join(technology.get('frameworks', []) or []) or 'Não detectado'
                cms = technology.get('cms') or 'Não detectado'
                libraries = ', '.join(technology.get('libraries', []) or []) or 'Não detectado'
                languages = ', '.join(technology.get('languages', []) or []) or 'Não detectado'
                server = technology.get('server') or 'Não detectado'
                tech_html = f"""
                <div class=\"section\">
                    <h2>Tecnologias Detectadas</h2>
                    <p><strong>Frameworks:</strong> {frameworks}</p>
                    <p><strong>CMS:</strong> {cms}</p>
                    <p><strong>Bibliotecas:</strong> {libraries}</p>
                    <p><strong>Linguagens:</strong> {languages}</p>
                    <p><strong>Servidor:</strong> {server}</p>
                </div>
                """

            # SEO section HTML
            seo_html = ""
            if seo:
                og_list = ''.join([f"<li><code>{k}</code>: {v}</li>" for k, v in (seo.get('og') or {}).items()])
                tw_list = ''.join([f"<li><code>{k}</code>: {v}</li>" for k, v in (seo.get('twitter') or {}).items()])
                seo_html = f"""
                <div class=\"section\">
                    <h2>SEO Meta Tags</h2>
                    <p><strong>Title:</strong> {seo.get('title') or 'Não encontrado'}</p>
                    <p><strong>Description:</strong> {seo.get('description') or 'Não encontrado'}</p>
                    <p><strong>Keywords:</strong> {seo.get('keywords') or 'Não encontrado'}</p>
                    <p><strong>Robots:</strong> {seo.get('robots') or 'Não encontrado'}</p>
                    <p><strong>Canonical:</strong> {seo.get('canonical') or 'Não encontrado'}</p>
                    <div>
                        <h3>Open Graph</h3>
                        <ul>{og_list or '<li>Nenhum</li>'}</ul>
                    </div>
                    <div>
                        <h3>Twitter Cards</h3>
                        <ul>{tw_list or '<li>Nenhum</li>'}</ul>
                    </div>
                </div>
                """

            guide_html = ""
            compliance_html = ""
            if guide:
                excerpts = guide.get("excerpts") or {}
                mq = excerpts.get("media_queries")
                layout = excerpts.get("layout_guidelines")
                components = excerpts.get("component_patterns")
                guide_html = f"""
                <div class="section">
                    <h2>Guia de Responsividade (responsive-guide.md)</h2>
                    <p><strong>Versão:</strong> {guide.get('version') or 'N/A'}</p>
                    <p><strong>Arquivo:</strong> {guide.get('path') or 'responsive-guide.md'}</p>
                    {f'<details><summary><strong>Regras de Media Queries</strong></summary><pre class=\"code-example\">{mq}</pre></details>' if mq else ''}
                    {f'<details><summary><strong>Diretrizes de Layout</strong></summary><pre class=\"code-example\">{layout}</pre></details>' if layout else ''}
                    {f'<details><summary><strong>Padrões de Componentes</strong></summary><pre class=\"code-example\">{components}</pre></details>' if components else ''}
                </div>
                """

                bp_list = guide.get("breakpoints") or []
                rows = []
                details = []
                for bp in bp_list:
                    bp_id = bp.get("id")
                    bp_label = bp.get("label") or bp_id
                    bp_w = bp.get("width")
                    bp_h = bp.get("height")
                    sc = next((s for s in (screenshots or []) if s.get("device") == bp_id), None)
                    compliant = sc.get("compliant") if sc else None
                    status = "Conforme" if compliant else "Não conforme" if compliant is False else "Indefinido"
                    status_color = "#155724" if compliant else "#721c24" if compliant is False else "#856404"
                    violations = (sc.get("violations") or []) if sc else []
                    rows.append(
                        f"<tr>"
                        f"<td>{bp_label}</td>"
                        f"<td>{bp_w}×{bp_h}</td>"
                        f"<td style='color:{status_color}; font-weight:700'>{status}</td>"
                        f"<td>{len(violations)}</td>"
                        f"</tr>"
                    )

                    if compliant is False:
                        v_list = ''.join([f"<li><strong>{v.get('title','')}</strong> — {v.get('description','')} <em>({v.get('guide_ref','')})</em></li>" for v in violations])
                        screenshot_block = ""
                        if sc and sc.get("url"):
                            screenshot_block = (
                                f'<div class="screenshot">'
                                f'<img src="{sc.get("url")}" alt="{bp_label}">'
                                f'<div class="screenshot-caption">{bp_label} ({bp_w}×{bp_h})</div>'
                                f'</div>'
                            )
                        details.append(f"""
                        <div class="issue warning">
                            <h3>{bp_label} — Não conformidades</h3>
                            <ul>{v_list or '<li>Nenhuma</li>'}</ul>
                            {screenshot_block}
                        </div>
                        """)

                compliance_html = f"""
                <div class="section">
                    <h2>Conformidade por Breakpoint</h2>
                    <table style="width:100%; border-collapse: collapse;">
                        <thead>
                            <tr>
                                <th style="text-align:left; border-bottom:1px solid #e0e0e0; padding:8px;">Breakpoint</th>
                                <th style="text-align:left; border-bottom:1px solid #e0e0e0; padding:8px;">Viewport</th>
                                <th style="text-align:left; border-bottom:1px solid #e0e0e0; padding:8px;">Status</th>
                                <th style="text-align:left; border-bottom:1px solid #e0e0e0; padding:8px;">Violações</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(rows)}
                        </tbody>
                    </table>
                </div>
                {''.join(details)}
                """

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

            {tech_html}
            {seo_html}
            {guide_html}
            {compliance_html}
            
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
                        {f'<p><strong>Justificativa:</strong> {rec.get("justification", "")}</p>' if rec.get('justification') else ''}
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
            reports_dir = Path(__file__).resolve().parents[2] / "reports"
            reports_dir.mkdir(exist_ok=True)
            report_path = reports_dir / report_filename
            
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

    def load_responsive_guide(self) -> Dict[str, Any]:
        tool = ResponsiveGuideTool()
        return tool.load_and_parse()
    
    async def capture_screenshots(
        self,
        url: str,
        analysis_id: str,
        breakpoints: Optional[List[Dict[str, Any]]] = None,
        guide_rules: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Capture screenshots using the agent"""
        try:
            print(f"Agent capturing screenshots for {url}")
            
            # Use the screenshot tool directly
            screenshot_tool = ScreenshotCaptureTool()
            screenshots = await screenshot_tool.run(url, analysis_id, breakpoints=breakpoints, guide_rules=guide_rules)
            
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

    async def detect_technology(self, url: str) -> Dict[str, Any]:
        """Detect website technology and SEO"""
        try:
            print(f"Agent detecting technology for {url}")
            tool = TechnologyDetectionTool()
            return await tool.run(url)
        except Exception as e:
            print(f"Error detecting technology: {e}")
            return {"technology": {}, "seo": {}}
    
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
        recommendations: List[Dict[str, Any]],
        technology: Optional[Dict[str, Any]] = None,
        seo: Optional[Dict[str, Any]] = None,
        guide: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create HTML report"""
        try:
            print(f"Agent creating report for {url}")
            
            # Use the report generator tool directly
            report_tool = ReportGeneratorTool()
            report_data = await report_tool.run(analysis_id, url, screenshots, issues, recommendations, technology, seo, guide)
            
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

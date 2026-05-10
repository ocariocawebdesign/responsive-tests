# 📐 Guia de Referência: Design Responsivo para IA
> **Projeto:** responsive-test  
> **Versão:** 1.0  
> **Fontes:** MDN Web Docs — Design Responsivo, CSS Reference + Práticas modernas com Tailwind CSS  
> **Finalidade:** Documento de referência para análise automatizada de responsividade em sites.

---

## 1. O QUE É DESIGN RESPONSIVO

Design Responsivo (RWD — Responsive Web Design) é um conjunto de práticas que permite que páginas web alterem seu **layout e aparência** para se adequar a diferentes larguras, resoluções e dispositivos. O termo foi cunhado por **Ethan Marcotte em 2010** e se apoia em três pilares fundamentais:

| Pilar | Descrição |
|---|---|
| **Grids Fluidas** | Layouts baseados em proporções percentuais e unidades flexíveis |
| **Imagens Fluidas** | Imagens que se adaptam ao container sem distorção |
| **Media Queries** | Regras CSS condicionais aplicadas por breakpoint |

> ⚠️ Design responsivo **não é uma tecnologia separada** — é uma abordagem, um conjunto de boas práticas.

---

## 2. FUNDAMENTOS CSS — VIEWPORT & META TAG

### 2.1 Meta Tag Obrigatória

Todo documento HTML responsivo deve conter no `<head>`:

```html
<meta name="viewport" content="width=device-width, initial-scale=1" />
```

**Por que é necessária:** Sem essa tag, navegadores mobile definem o viewport padrão como 960px (legado do iPhone original), o que impede que media queries funcionem corretamente.

**Parâmetros aceitos:**

| Parâmetro | Valor recomendado | Observação |
|---|---|---|
| `width` | `device-width` | Obrigatório |
| `initial-scale` | `1` | Obrigatório |
| `minimum-scale` | — | **Evitar** — prejudica acessibilidade |
| `maximum-scale` | — | **Evitar** — prejudica acessibilidade |
| `user-scalable` | — | **Nunca usar `no`** — viola acessibilidade |

---

## 3. MEDIA QUERIES — REFERÊNCIA COMPLETA

### 3.1 Sintaxe Base

```css
@media <tipo> and (<condição>) {
  /* regras CSS */
}
```

### 3.2 Tipos de Mídia

| Tipo | Uso |
|---|---|
| `screen` | Telas (padrão em RWD) |
| `print` | Impressão |
| `all` | Todos os dispositivos |

### 3.3 Breakpoints — Abordagem Mobile First

A abordagem **mobile first** define estilos base para mobile e sobrescreve para telas maiores:

```css
/* Base: mobile */
.container { padding: 1rem; }

/* Tablet */
@media screen and (min-width: 768px) {
  .container { padding: 2rem; }
}

/* Desktop */
@media screen and (min-width: 1024px) {
  .container { padding: 3rem; max-width: 1200px; margin: 0 auto; }
}

/* Wide */
@media screen and (min-width: 1280px) {
  .container { max-width: 1440px; }
}
```

### 3.4 Breakpoints Padrão do Ecossistema

| Nome | CSS puro | Tailwind CSS |
|---|---|---|
| **Mobile** | `< 640px` | (base, sem prefixo) |
| **sm** | `≥ 640px` | `sm:` |
| **md** | `≥ 768px` | `md:` |
| **lg** | `≥ 1024px` | `lg:` |
| **xl** | `≥ 1280px` | `xl:` |
| **2xl** | `≥ 1536px` | `2xl:` |

### 3.5 Operadores de Media Query

```css
/* AND — ambas as condições */
@media screen and (min-width: 768px) and (max-width: 1023px) { }

/* OR (vírgula) — qualquer das condições */
@media screen and (min-width: 768px), print { }

/* NOT */
@media not screen { }

/* Orientação */
@media (orientation: landscape) { }
@media (orientation: portrait) { }

/* Preferências do usuário */
@media (prefers-color-scheme: dark) { }
@media (prefers-reduced-motion: reduce) { }
@media (hover: none) { } /* touch devices */
```

---

## 4. LAYOUTS MODERNOS — CSS GRID & FLEXBOX

### 4.1 Flexbox — Padrões Responsivos

```css
/* Container base */
.flex-container {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

/* Items crescem igualmente */
.flex-item {
  flex: 1 1 300px; /* grow | shrink | basis */
}

/* Auto-layout responsivo sem media queries */
.flex-auto {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}
.flex-auto > * {
  flex: 1 1 min(100%, 300px);
}
```

**Propriedades chave:**

| Propriedade | Valores comuns | Efeito |
|---|---|---|
| `flex-direction` | `row`, `column` | Eixo principal |
| `flex-wrap` | `wrap`, `nowrap` | Quebra de linha |
| `justify-content` | `flex-start`, `center`, `space-between`, `space-around` | Alinhamento horizontal |
| `align-items` | `stretch`, `center`, `flex-start`, `flex-end` | Alinhamento vertical |
| `gap` | qualquer valor | Espaço entre items |
| `flex` | `1`, `auto`, `none`, `1 1 200px` | Atalho grow/shrink/basis |

### 4.2 CSS Grid — Padrões Responsivos

```css
/* Grid responsivo com auto-fill */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

/* Grid de layout (ex: sidebar + conteúdo) */
.layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

@media (min-width: 768px) {
  .layout {
    grid-template-columns: 250px 1fr;
  }
}

/* Grid com áreas nomeadas */
.page {
  display: grid;
  grid-template-areas:
    "header"
    "nav"
    "main"
    "aside"
    "footer";
}

@media (min-width: 1024px) {
  .page {
    grid-template-columns: 200px 1fr 200px;
    grid-template-areas:
      "header header header"
      "nav    main   aside"
      "footer footer footer";
  }
}
```

**Propriedades chave:**

| Propriedade | Valores comuns | Efeito |
|---|---|---|
| `grid-template-columns` | `1fr 1fr`, `repeat(3, 1fr)`, `minmax(200px, 1fr)` | Define colunas |
| `grid-template-rows` | `auto`, valores fixos ou `fr` | Define linhas |
| `gap` | qualquer valor | Espaço entre células |
| `auto-fill` | — | Cria o máximo de colunas que couber |
| `auto-fit` | — | Colapsa colunas vazias, expandindo as ocupadas |
| `minmax(min, max)` | `minmax(200px, 1fr)` | Range de tamanho de track |

### 4.3 Multi-column Layout

```css
/* Número fixo de colunas */
.multicol {
  column-count: 3;
  column-gap: 2rem;
}

/* Largura mínima — número de colunas automático */
.multicol-auto {
  column-width: 200px;
}
```

---

## 5. TIPOGRAFIA RESPONSIVA

### 5.1 Com Media Queries

```css
html { font-size: 1rem; }

h1 { font-size: 1.75rem; }

@media (min-width: 768px) {
  h1 { font-size: 2.5rem; }
}

@media (min-width: 1200px) {
  h1 { font-size: 4rem; }
}
```

### 5.2 Com Unidades de Viewport (Recomendado)

```css
/* ERRADO — impede zoom por acessibilidade */
h1 { font-size: 6vw; }

/* CORRETO — vw + rem garantem escala e zoom */
h1 { font-size: calc(1.5rem + 3vw); }
p  { font-size: calc(1rem + 0.5vw); }
```

### 5.3 CSS Clamp (Moderno)

```css
/* clamp(mínimo, preferencial, máximo) */
h1 { font-size: clamp(1.75rem, 5vw, 4rem); }
p  { font-size: clamp(1rem, 2vw, 1.25rem); }
```

> ✅ `clamp()` é a forma mais elegante de tipografia fluida — sem media queries, com controle total de limites.

---

## 6. IMAGENS RESPONSIVAS

### 6.1 CSS Base

```css
img, video, embed, object {
  max-width: 100%;
  height: auto;
}
```

### 6.2 HTML Avançado — srcset e sizes

```html
<!-- Imagem adaptativa por resolução -->
<img
  src="foto-800.jpg"
  srcset="foto-400.jpg 400w, foto-800.jpg 800w, foto-1200.jpg 1200w"
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 800px"
  alt="Descrição da imagem"
  loading="lazy"
/>
```

### 6.3 HTML Avançado — Art Direction com `<picture>`

```html
<picture>
  <!-- Mobile: imagem quadrada/recortada -->
  <source media="(max-width: 640px)" srcset="hero-mobile.jpg" />
  <!-- Tablet -->
  <source media="(max-width: 1024px)" srcset="hero-tablet.jpg" />
  <!-- Desktop: imagem landscape completa -->
  <img src="hero-desktop.jpg" alt="Hero banner" />
</picture>
```

### 6.4 Imagem de Fundo Responsiva

```css
.hero {
  background-image: url('hero-mobile.jpg');
  background-size: cover;
  background-position: center;
}

@media (min-width: 768px) {
  .hero { background-image: url('hero-desktop.jpg'); }
}
```

---

## 7. UNIDADES CSS — REFERÊNCIA

| Unidade | Tipo | Relativa a | Uso recomendado |
|---|---|---|---|
| `px` | Absoluta | — | Bordas, shadows, valores fixos |
| `rem` | Relativa | Fonte raiz (`<html>`) | Tipografia, padding, margin |
| `em` | Relativa | Elemento pai | Componentes autocontidos |
| `%` | Relativa | Elemento pai | Larguras fluidas |
| `vw` | Viewport | Largura do viewport | Hero sections, fluid type |
| `vh` | Viewport | Altura do viewport | Full-screen sections |
| `vmin` | Viewport | Menor dimensão | Elementos quadrados responsivos |
| `vmax` | Viewport | Maior dimensão | — |
| `fr` | Grid | Espaço disponível | Colunas de grid |
| `ch` | Tipográfica | Largura do "0" | Max-width de texto |
| `svh/dvh/lvh` | Viewport (moderno) | Viewport dinâmico/small/large | Mobile fullscreen |

---

## 8. PROPRIEDADES CSS MODERNAS PARA RESPONSIVIDADE

### 8.1 Container Queries (CSS moderno)

```css
/* Define o container de referência */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

/* Query baseada no container, não no viewport */
@container card (min-width: 400px) {
  .card { display: flex; }
}
```

### 8.2 Logical Properties (para RTL e internacionalização)

```css
/* Em vez de left/right, usar start/end */
.element {
  margin-inline: auto;      /* margin-left + margin-right */
  padding-block: 2rem;      /* padding-top + padding-bottom */
  border-inline-start: 4px solid blue; /* border-left (LTR) */
}
```

### 8.3 CSS Custom Properties para temas responsivos

```css
:root {
  --spacing-base: 1rem;
  --font-size-body: clamp(1rem, 1.5vw, 1.125rem);
  --max-width: 1280px;
}

@media (min-width: 768px) {
  :root {
    --spacing-base: 1.5rem;
  }
}
```

---

## 9. TAILWIND CSS — REFERÊNCIA DE RESPONSIVIDADE

### 9.1 Prefixos de Breakpoint (Mobile First)

```html
<!-- Classe aplicada APENAS em md e acima -->
<div class="block md:flex lg:grid">...</div>

<!-- Grid responsivo -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  ...
</div>
```

### 9.2 Padrões de Layout Responsivo com Tailwind

```html
<!-- Sidebar layout -->
<div class="flex flex-col lg:flex-row gap-6">
  <aside class="w-full lg:w-64 shrink-0">...</aside>
  <main class="flex-1 min-w-0">...</main>
</div>

<!-- Cards responsivos -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
  <div class="rounded-xl shadow p-4">...</div>
</div>

<!-- Hero responsivo -->
<section class="px-4 py-12 sm:px-6 sm:py-16 lg:px-8 lg:py-24 xl:py-32">
  <h1 class="text-3xl sm:text-4xl lg:text-5xl xl:text-6xl font-bold">...</h1>
</section>
```

### 9.3 Tipografia Responsiva com Tailwind

```html
<h1 class="text-2xl sm:text-3xl md:text-4xl lg:text-5xl xl:text-6xl font-bold">
  Título
</h1>
<p class="text-base sm:text-lg lg:text-xl text-gray-600">
  Parágrafo
</p>
```

### 9.4 Espaçamento Responsivo com Tailwind

```html
<div class="p-4 sm:p-6 md:p-8 lg:p-12">
  <div class="space-y-4 sm:space-y-6 lg:space-y-8">
    ...
  </div>
</div>
```

### 9.5 Visibilidade Responsiva com Tailwind

```html
<!-- Visível apenas em mobile -->
<div class="block md:hidden">Menu hambúrguer</div>

<!-- Visível apenas em desktop -->
<nav class="hidden md:flex items-center gap-6">...</nav>
```

### 9.6 Imagens com Tailwind

```html
<img
  src="foto.jpg"
  class="w-full h-auto object-cover rounded-lg"
  alt="Imagem responsiva"
/>

<!-- Imagem com aspect ratio fixo -->
<div class="aspect-video w-full overflow-hidden rounded-lg">
  <img src="video-thumb.jpg" class="w-full h-full object-cover" />
</div>
```

### 9.7 Tailwind — Classes de Container

```html
<!-- Container com padding automático -->
<div class="container mx-auto px-4 sm:px-6 lg:px-8">...</div>

<!-- Max-width manual -->
<div class="w-full max-w-7xl mx-auto px-4">...</div>
```

---

## 10. CHECKLIST DE ANÁLISE RESPONSIVA

Use este checklist para avaliar qualquer site ou componente:

### 10.1 Meta & HTML Base
- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` presente
- [ ] `lang` definido no `<html>`
- [ ] Estrutura semântica com `<header>`, `<main>`, `<footer>`, `<nav>`, `<aside>`

### 10.2 Layout
- [ ] Layout não quebra em 320px (iPhone SE)
- [ ] Layout funciona em 375px (iPhone padrão)
- [ ] Layout funciona em 768px (iPad)
- [ ] Layout funciona em 1024px (laptop)
- [ ] Layout funciona em 1440px+ (desktop wide)
- [ ] Não há scroll horizontal indesejado em nenhum breakpoint
- [ ] Colunas colapsam adequadamente em mobile
- [ ] Sidebar/drawer ocultos em mobile com alternativa funcional

### 10.3 Tipografia
- [ ] Tamanho mínimo de fonte: `16px` (`1rem`) para corpo
- [ ] Comprimento de linha: entre 45–75 caracteres (`max-width: 65ch`)
- [ ] Escala de tipo responsiva aplicada
- [ ] Contraste de cor mínimo: 4.5:1 (WCAG AA)

### 10.4 Imagens & Mídia
- [ ] `max-width: 100%; height: auto` em todas as imagens
- [ ] `srcset` ou `<picture>` para imagens críticas (hero, banners)
- [ ] `loading="lazy"` em imagens fora da área visível
- [ ] Vídeos e embeds com container responsivo (`aspect-ratio` ou padding trick)

### 10.5 Interação & Toque
- [ ] Área de toque mínima: 44×44px (recomendação Apple/Google)
- [ ] Espaço entre elementos clicáveis: mínimo 8px
- [ ] Formulários usáveis em mobile (campos grandes, teclado correto)
- [ ] Menu de navegação acessível em mobile

### 10.6 Performance Responsiva
- [ ] Imagens servidas no tamanho adequado para o dispositivo
- [ ] CSS não carrega recursos pesados desnecessários para mobile
- [ ] Fontes com `font-display: swap`

### 10.7 Acessibilidade (a11y)
- [ ] `user-scalable=no` ausente (deve permitir zoom)
- [ ] Foco visível em todos os elementos interativos
- [ ] ARIA labels em ícones e botões sem texto
- [ ] Ordem de foco lógica no fluxo do documento

---

## 11. ANTIPADRÕES — O QUE EVITAR

| Antipadrão | Por que é ruim | Alternativa |
|---|---|---|
| `width: 100vw` em elementos | Causa scroll horizontal | `width: 100%` ou `max-width: 100vw` |
| `overflow: hidden` no body | Oculta conteúdo legítimo | Identificar e corrigir a causa |
| `user-scalable=no` | Quebra acessibilidade | Remover completamente |
| Pixels fixos em containers (`width: 960px`) | Não adapta ao dispositivo | Usar `max-width` com `%` ou `rem` |
| Font-size abaixo de 14px em mobile | Ilegível | Mínimo 16px para corpo |
| Hover como único mecanismo de interação | Não funciona em touch | Fornecer alternativa para toque |
| `height: 100vh` em mobile | Quebra em browsers mobile que somem a barra de endereço | Usar `height: 100svh` com fallback |
| Z-index excessivo | Conflitos de camada em mobile | Usar contextos de empilhamento previsíveis |

---

## 12. SNIPPETS PRONTOS — PADRÕES COMUNS

### 12.1 Viewport Height Correta para Mobile

```css
/* Fallback */
.fullscreen { height: 100vh; }

/* Moderno — exclui barra do navegador */
@supports (height: 100svh) {
  .fullscreen { height: 100svh; }
}
```

### 12.2 Grid Responsivo sem Media Queries

```css
.auto-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 280px), 1fr));
  gap: 1.5rem;
}
```

### 12.3 Container com Padding Responsivo

```css
.container {
  width: 100%;
  max-width: 1280px;
  margin-inline: auto;
  padding-inline: clamp(1rem, 5vw, 3rem);
}
```

### 12.4 Texto que Não Quebra em Uma Linha (Truncate)

```css
.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}
```

### 12.5 Aspect Ratio Responsivo

```css
/* Moderno */
.video-wrapper {
  aspect-ratio: 16 / 9;
  width: 100%;
  overflow: hidden;
}

/* Fallback legado */
.video-wrapper-legacy {
  position: relative;
  padding-bottom: 56.25%; /* 16:9 */
  height: 0;
}
.video-wrapper-legacy > * {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
```

---

## 13. REFERÊNCIAS

| Recurso | URL |
|---|---|
| MDN — Design Responsivo | https://developer.mozilla.org/pt-BR/docs/Learn_web_development/Core/CSS_layout/Responsive_Design |
| MDN — Media Queries | https://developer.mozilla.org/pt-BR/docs/Web/CSS/Guides/Media_queries |
| MDN — CSS Reference | https://developer.mozilla.org/pt-BR/docs/Web/CSS |
| MDN — Imagens Responsivas | https://developer.mozilla.org/pt-BR/docs/Web/HTML/Guides/Responsive_images |
| Tailwind CSS Docs | https://tailwindcss.com/docs |
| Tailwind — Responsive Design | https://tailwindcss.com/docs/responsive-design |
| WCAG 2.1 — Acessibilidade | https://www.w3.org/TR/WCAG21/ |

---

*Documento gerado para uso como referência de análise de IA no projeto responsive-test.*  
*Fontes: MDN Web Docs + Práticas modernas com Tailwind CSS v3/v4.*
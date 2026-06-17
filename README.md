# Vahhab Piranfar — Personal Research Website

Academic portfolio and research hub for **Vahhab Piranfar**, Molecular Microbiologist, Bioinformatician, and EB-1A recipient.

**Live site:** [vahhabpiranfar.com](https://vahhabpiranfar.com)

---

## Overview

A custom-designed academic website built with [Quarto](https://quarto.org/) and hosted on GitHub Pages. The site showcases research publications, active software projects, scientific blog posts, and professional background — with a fully custom design system on top of the Cosmo theme.

Featured projects include the [AI Bacteriology Hub](https://vahhabpiranfar.com/projects/ai-bacteriology-hub.html) — a full-stack computational microbiology platform with an AI Research Layer, manifest-driven lab tools, and Docker-sandboxed Python execution — as well as tools for [USCIS case tracking](https://piranfar.github.io/USCIS-Tracker/) and [Crossref citation formatting](https://piranfar.github.io/Crossref-Reference-Formatter/).

---

## Live Pages

| Page | URL | Description |
|------|-----|-------------|
| **Home** | [vahhabpiranfar.com](https://vahhabpiranfar.com) | Hero section with research summary, key stats (650+ citations), and focus areas |
| **Projects** | [vahhabpiranfar.com/projects.html](https://vahhabpiranfar.com/projects.html) | Featured project cards and full project archive |
| **AI Bacteriology Hub** | [vahhabpiranfar.com/projects/ai-bacteriology-hub.html](https://vahhabpiranfar.com/projects/ai-bacteriology-hub.html) | Dedicated deep-dive page for the AI Bacteriology Hub platform |
| **Discuss & Review** | [vahhabpiranfar.com/blog.html](https://vahhabpiranfar.com/blog.html) | Blog with scientific commentary, paper reviews, and data essays |
| **About** | [vahhabpiranfar.com/about.html](https://vahhabpiranfar.com/about.html) | Professional profile, research interests, experience timeline, and technical skills |
| **Publications** | [vahhabpiranfar.com/publications.html](https://vahhabpiranfar.com/publications.html) | 33+ peer-reviewed publications with citation cards and academic profile badges |

### Blog Posts

| Post | URL |
|------|-----|
| Antibiotic Persistence | [vahhabpiranfar.com/posts/antibiotic-persistence.html](https://vahhabpiranfar.com/posts/antibiotic-persistence.html) |
| Unemployment Paradox | [vahhabpiranfar.com/posts/unemployment-paradox.html](https://vahhabpiranfar.com/posts/unemployment-paradox.html) |
| Discuss & Review | [vahhabpiranfar.com/posts/discuss.html](https://vahhabpiranfar.com/posts/discuss.html) |

---

## Featured Projects

### [AI Bacteriology Hub](https://vahhabpiranfar.com/projects/ai-bacteriology-hub.html)

A production-grade full-stack research platform for computational bacteriology. Combines a curated scientific knowledge base, an **AI Research Layer** for interactive AMR reasoning (server-side AI proxy, streaming SSE, provider-agnostic gateway), and **manifest-driven Python lab tools** executed inside a hardened Docker sandbox.

Key capabilities:
- **AMR Simulator** — AI reasoning over pathogen/antibiotic combinations, resistance mechanisms, and breakpoints
- **AI Protocol Drafter** — streaming SOP and research abstract generation
- **Manifest-driven lab apps** — upload a ZIP with `manifest.json` + `main.py`, the React frontend auto-builds all forms and output renderers with no code changes
- **AI Orchestrator** — internal pipeline for AI-proposed lab app upgrades with human-in-the-loop review
- **Docker sandbox** — isolated execution with no network, resource caps, and configurable timeouts
- **Google Cloud Run deployment** — multi-stage Dockerfile, PostgreSQL (Cloud SQL), Secret Manager, WhiteNoise static serving

Stack: Django 4.2 · Django REST Framework · React 18 · Vite 5 · Tailwind CSS · Docker · PostgreSQL · Google Cloud Run

Live: [ai-bacteriology.vahhabpiranfar.com](https://ai-bacteriology.vahhabpiranfar.com/) · Deep-dive: [vahhabpiranfar.com/projects/ai-bacteriology-hub.html](https://vahhabpiranfar.com/projects/ai-bacteriology-hub.html)

---

### [USCIS Case Tracker](https://piranfar.github.io/USCIS-Tracker/)

Real-time immigration case status monitoring and analytics. Automated data collection, visualization dashboards, and historical trend analysis for USCIS case progression.

Stack: Python · Data Visualization · Web Scraping

---

### [Crossref Reference Formatter](https://piranfar.github.io/Crossref-Reference-Formatter/)

Paste Crossref references and export Vancouver-style linked citations. Converts bibliographic metadata into formatted citations with rich text, Word, and HTML export options.

Stack: JavaScript · Crossref API · Citation Formatting

---

## Tech Stack

- **Quarto** — static site generator with Markdown/YAML authoring
- **Custom CSS** — 1,300+ lines: design tokens, component library (hero, feature cards, citation cards, project cards, skill pills, academic badges), Inter + Outfit typography, responsive layout
- **GitHub Pages** — deployed from the `docs/` output directory
- **Google Tag Manager** — analytics via `gtm-head.html` / `gtm-body.html`
- **Google Fonts** — Inter (body) + Outfit (headings)

---

## Project Structure

```
├── _quarto.yml              # Site config, navbar, footer, format settings
├── index.qmd                # Homepage with hero section
├── about.qmd                # Professional profile and skills
├── projects.qmd             # Project showcase (featured cards + archive table)
├── projects/
│   └── ai-bacteriology-hub.qmd   # AI Bacteriology Hub deep-dive page
├── publications.qmd         # Academic publications list
├── blog.qmd                 # Blog listing page
├── posts/                   # Blog post source files
│   ├── antibiotic-persistence.qmd
│   ├── discuss.qmd
│   └── unemployment-paradox.qmd
├── styles.css               # Full custom design system
├── profile.jpg              # Profile photo
├── gtm-head.html            # Google Tag Manager (head)
├── gtm-body.html            # Google Tag Manager (body)
├── docs/                    # Rendered output (GitHub Pages root)
│   ├── sitemap.xml          # Auto-generated sitemap (all pages)
│   └── robots.txt           # Points crawlers to sitemap
└── _freeze/                 # Quarto compute cache
```

---

## SEO

The site includes:
- **Sitemap** at [vahhabpiranfar.com/sitemap.xml](https://vahhabpiranfar.com/sitemap.xml) — auto-generated by Quarto on every render, covering all pages with `lastmod` timestamps
- **robots.txt** at [vahhabpiranfar.com/robots.txt](https://vahhabpiranfar.com/robots.txt) — references the sitemap for crawler discovery
- Semantic HTML structure with proper heading hierarchy across all pages
- Descriptive `<title>` and metadata from Quarto's HTML format settings

---

## Local Development

**Prerequisites:** [Quarto CLI](https://quarto.org/docs/get-started/)

```bash
# Preview with live reload
quarto preview

# Build the site
quarto render
```

The rendered site is written to `docs/`. Commit and push to deploy.

---

## Deployment

Pushes to the `main` branch publish the `docs/` directory through GitHub Pages. No CI pipeline needed — render locally and push.

---

## Links

- [Google Scholar](https://scholar.google.com/citations?user=o2GdH2oAAAAJ&hl=en)
- [ORCID](https://orcid.org/0000-0003-3653-5739)
- [LinkedIn](https://www.linkedin.com/in/vahhab-piranfar/)
- [GitHub](https://github.com/piranfar)
- [ResearchGate](https://www.researchgate.net/profile/Vahhab-Piranfar)

---

© 2026 Vahhab Piranfar

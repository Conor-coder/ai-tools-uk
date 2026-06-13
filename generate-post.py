#!/usr/bin/env python3
"""
AIToolsUK — Daily Blog Post Generator
Generates a 1,200-word SEO-optimised HTML blog post using Claude,
saves it to blog/<slug>.html, updates blog/index.html and sitemap.xml,
then optionally commits and pushes to GitHub.

Usage:
    python3 generate-post.py           # generate + save
    python3 generate-post.py --push    # generate + save + git commit + push
    python3 generate-post.py --dry-run # print chosen topic without generating
"""

import os
import sys
import re
import datetime
import subprocess

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SITE_DIR  = os.path.dirname(os.path.abspath(__file__))
BLOG_DIR  = os.path.join(SITE_DIR, "blog")
INDEX     = os.path.join(BLOG_DIR, "index.html")
SITEMAP   = os.path.join(SITE_DIR, "sitemap.xml")
ENV_FILE  = os.path.join(os.path.dirname(SITE_DIR), ".env")  # ~/jarvis/.env
BASE_URL  = "https://aitoolsuk.com"

# ---------------------------------------------------------------------------
# Topic pool  (slug, title, category, emoji, gradient-css)
# Add new rows here to extend the queue indefinitely.
# ---------------------------------------------------------------------------

TOPICS = [
    ("semrush-uk-small-business",
     "Semrush for UK Small Businesses: Is It Worth the Price in 2026?",
     "SEO Tools", "🔍",
     "rgba(255,107,107,0.3), rgba(108,99,255,0.2)"),

    ("notion-ai-uk-business",
     "Notion AI for UK Small Businesses: The Ultimate Productivity Tool?",
     "Productivity", "📋",
     "rgba(0,212,170,0.3), rgba(108,99,255,0.2)"),

    ("monday-com-uk-teams",
     "Monday.com for UK Small Business Teams: A Complete Review 2026",
     "Project Management", "📊",
     "rgba(108,99,255,0.3), rgba(255,107,107,0.2)"),

    ("hostinger-uk-website",
     "Best Web Hosting for UK Small Businesses in 2026: Hostinger Reviewed",
     "Web Hosting", "🌐",
     "rgba(0,212,170,0.25), rgba(255,107,107,0.2)"),

    ("chatgpt-vs-claude-uk",
     "ChatGPT vs Claude for UK Business: Which AI Assistant Wins in 2026?",
     "AI Assistants", "🤖",
     "rgba(108,99,255,0.35), rgba(0,212,170,0.2)"),

    ("ai-social-media-uk",
     "Best AI Social Media Tools for UK Small Businesses in 2026",
     "Social Media", "📱",
     "rgba(255,107,107,0.25), rgba(0,212,170,0.2)"),

    ("ai-email-marketing-uk",
     "AI Email Marketing Tools for UK Small Businesses: The 2026 Guide",
     "Email Marketing", "📧",
     "rgba(0,212,170,0.3), rgba(255,107,107,0.2)"),

    ("ai-hr-uk-small-business",
     "AI HR Tools for UK Small Businesses: Automate Recruitment and Payroll in 2026",
     "HR & Payroll", "👥",
     "rgba(108,99,255,0.25), rgba(255,107,107,0.2)"),

    ("ai-ecommerce-uk",
     "AI Tools for UK E-Commerce Businesses: Boost Sales with Automation in 2026",
     "E-Commerce", "🛒",
     "rgba(255,107,107,0.3), rgba(108,99,255,0.2)"),

    ("grammarly-vs-claude-uk",
     "Grammarly vs Claude for UK Business Writing: Which Should You Use in 2026?",
     "Writing Tools", "✍️",
     "rgba(0,212,170,0.3), rgba(108,99,255,0.2)"),

    ("ai-website-builder-uk",
     "Best AI Website Builders for UK Small Businesses in 2026",
     "Web Design", "🎨",
     "rgba(108,99,255,0.3), rgba(0,212,170,0.25)"),

    ("ai-crm-uk",
     "Best AI CRM Tools for UK Small Businesses: Manage Customers Smarter in 2026",
     "CRM", "💼",
     "rgba(255,107,107,0.25), rgba(0,212,170,0.2)"),

    ("notion-vs-monday-uk",
     "Notion vs Monday.com for UK Small Businesses: Which Wins in 2026?",
     "Productivity", "⚡",
     "rgba(0,212,170,0.25), rgba(108,99,255,0.2)"),

    ("ai-video-uk-business",
     "Best AI Video Tools for UK Small Business Marketing in 2026",
     "Video Marketing", "🎬",
     "rgba(108,99,255,0.3), rgba(255,107,107,0.2)"),

    ("microsoft-copilot-uk",
     "Microsoft Copilot for UK Small Businesses: Honest Review 2026",
     "AI Assistants", "🤖",
     "rgba(0,212,170,0.3), rgba(108,99,255,0.2)"),

    ("ai-customer-feedback-uk",
     "AI Tools for Collecting and Analysing Customer Feedback in the UK",
     "Customer Service", "💬",
     "rgba(255,107,107,0.3), rgba(0,212,170,0.2)"),

    ("ai-legal-uk",
     "AI Legal Tools for UK Small Businesses: Contracts, GDPR and Compliance in 2026",
     "Legal", "⚖️",
     "rgba(108,99,255,0.25), rgba(255,107,107,0.2)"),

    ("awin-affiliate-uk",
     "How UK Small Businesses Can Make Money with Affiliate Marketing via Awin",
     "Affiliate Marketing", "💰",
     "rgba(0,212,170,0.3), rgba(108,99,255,0.25)"),

    ("ai-scheduling-uk",
     "AI Scheduling and Calendar Tools for UK Business Owners in 2026",
     "Productivity", "📅",
     "rgba(255,107,107,0.25), rgba(108,99,255,0.2)"),

    ("canva-alternatives-uk",
     "Best Canva Alternatives for UK Small Businesses in 2026",
     "Design Tools", "🎨",
     "rgba(108,99,255,0.3), rgba(0,212,170,0.2)"),

    ("ai-accounting-sole-trader-uk",
     "Best AI Accounting Tools for UK Sole Traders in 2026",
     "Accounting", "💷",
     "rgba(0,212,170,0.3), rgba(255,107,107,0.2)"),

    ("ai-retail-uk",
     "AI Tools for UK Independent Retailers: A Practical 2026 Guide",
     "Retail", "🛍️",
     "rgba(255,107,107,0.3), rgba(0,212,170,0.2)"),

    ("semrush-vs-ahrefs-uk",
     "Semrush vs Ahrefs for UK Small Businesses: Which SEO Tool Is Worth It?",
     "SEO Tools", "🔍",
     "rgba(108,99,255,0.3), rgba(255,107,107,0.2)"),

    ("ai-proposal-writing-uk",
     "AI Tools for Writing Business Proposals: A UK Small Business Guide",
     "Writing Tools", "📄",
     "rgba(0,212,170,0.3), rgba(108,99,255,0.2)"),

    ("zapier-alternatives-uk",
     "Best Zapier Alternatives for UK Small Businesses in 2026",
     "Automation", "🔗",
     "rgba(255,107,107,0.25), rgba(108,99,255,0.2)"),
]

# Affiliate links to weave into generated posts where relevant
AFFILIATE_LINKS = {
    "Claude":      ("https://claude.ai", "Try Claude Free"),
    "Canva":       ("https://www.canva.com/pro/", "Try Canva Pro"),
    "QuickBooks":  ("https://quickbooks.intuit.com/uk/", "Try QuickBooks UK"),
    "Jasper":      ("https://www.jasper.ai", "Try Jasper AI"),
    "Zapier":      ("https://zapier.com", "Try Zapier Free"),
    "Tidio":       ("https://www.tidio.com", "Try Tidio Free"),
    "Semrush":     ("https://www.semrush.com/", "Try Semrush"),
    "Notion":      ("https://www.notion.so/", "Try Notion Free"),
    "Monday.com":  ("https://monday.com/", "Try Monday.com"),
    "Hostinger":   ("https://www.hostinger.co.uk/", "Get Hostinger"),
    "Awin":        ("https://www.awin.com/", "Join Awin"),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    if k.strip() == "ANTHROPIC_API_KEY":
                        return v.strip()
    return None


def existing_slugs():
    slugs = set()
    for f in os.listdir(BLOG_DIR):
        if f.endswith(".html") and f != "index.html":
            slugs.add(f[:-5])
    return slugs


def pick_topic():
    done = existing_slugs()
    for slug, title, category, emoji, gradient in TOPICS:
        if slug not in done:
            return slug, title, category, emoji, gradient
    return None, None, None, None, None


def build_affiliate_context(title):
    """Return a short context string listing which affiliate tools are relevant."""
    lines = []
    for name, (url, cta) in AFFILIATE_LINKS.items():
        if name.lower() in title.lower():
            lines.append(f"  - {name}: {url} (CTA: \"{cta}\")")
    if not lines:
        # Fall back to listing core tools
        for name in ["Claude", "Jasper", "Zapier"]:
            url, cta = AFFILIATE_LINKS[name]
            lines.append(f"  - {name}: {url} (CTA: \"{cta}\")")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------

def generate_body(client, slug, title, category):
    today_year = datetime.date.today().year
    aff_ctx = build_affiliate_context(title)

    prompt = f"""Write a 1,200-word SEO-optimised blog post for AIToolsUK (aitoolsuk.com), a UK small business AI tools review site.

ARTICLE DETAILS
Title: {title}
Category: {category}
Primary keyword: {title.lower().split(":")[0].strip()}
Target audience: UK small business owners and sole traders
Tone: Professional, direct, British English (colour/practise/organise etc.)

CONTENT REQUIREMENTS
- Exactly 1,200 words of body content
- Compelling opening paragraph that addresses a UK business owner's pain point
- 4–6 <h2> headings that use natural keyword variations
- At least 2 <h3> subheadings under relevant h2 sections
- 2–3 <ul> or <ol> lists (use <li> items)
- 1 info/callout box (wrap it: <div class="info-box fade-in"><p>content</p></div>)
- A clear conclusion paragraph with a call to action
- Naturally weave in the year {today_year} where relevant

INTERNAL LINKS (use these exactly)
- Link text "our full AI tools guide" → href="best-ai-tools-uk-small-business.html"
- Link text "browse our top-rated tools" → href="../index.html#tools"

AFFILIATE LINKS (include 1–2 as <a> tags with rel="nofollow sponsored" target="_blank")
{aff_ctx}
Format affiliate CTAs as: <a href="URL" class="btn-tool" rel="nofollow sponsored" target="_blank">CTA TEXT →</a>

HTML OUTPUT RULES
- Output ONLY the HTML that goes inside <main class="article-body"> — no <html>, <head>, <body>, no nav, no footer
- Use only: <h2>, <h3>, <p>, <ul>, <ol>, <li>, <strong>, <em>, <a>, <div class="info-box fade-in">
- Add class="fade-in" to every <h2> and <p> element
- No markdown, no code fences, no explanations — raw HTML only
"""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        system=(
            "You are a professional UK technology journalist. Write in British English. "
            "Output ONLY the HTML article body as specified — no wrappers, no commentary."
        ),
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


# ---------------------------------------------------------------------------
# HTML page assembly
# ---------------------------------------------------------------------------

PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en-GB">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | AIToolsUK</title>
  <meta name="description" content="{meta_desc}">
  <link rel="canonical" href="{base_url}/blog/{slug}.html">

  <meta property="og:type"                   content="article">
  <meta property="og:url"                    content="{base_url}/blog/{slug}.html">
  <meta property="og:title"                  content="{title}">
  <meta property="og:description"            content="{meta_desc}">
  <meta property="og:image"                  content="{base_url}/og-image.png">
  <meta property="og:article:published_time" content="{iso_date}T09:00:00+01:00">
  <meta name="twitter:card"                  content="summary_large_image">
  <meta name="twitter:title"                 content="{title}">
  <meta name="twitter:description"           content="{meta_desc}">

  <link rel="stylesheet" href="../style.css">
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-XXXXXXXXXX');</script>

  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{title}",
    "datePublished": "{iso_date}T09:00:00+01:00",
    "dateModified":  "{iso_date}T09:00:00+01:00",
    "author": {{"@type": "Person", "name": "AIToolsUK Editorial Team", "url": "{base_url}/about.html"}},
    "publisher": {{"@type": "Organization", "name": "AIToolsUK", "url": "{base_url}"}},
    "mainEntityOfPage": {{"@type": "WebPage", "@id": "{base_url}/blog/{slug}.html"}}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{"@type": "ListItem", "position": 1, "name": "Home", "item": "{base_url}/"}},
      {{"@type": "ListItem", "position": 2, "name": "Blog", "item": "{base_url}/blog/"}},
      {{"@type": "ListItem", "position": 3, "name": "{title}"}}
    ]
  }}
  </script>
</head>
<body>

  <nav class="nav scrolled" id="nav" role="navigation" aria-label="Main navigation">
    <div class="nav-inner">
      <a href="../index.html" class="nav-logo">⚡ AIToolsUK</a>
      <ul class="nav-links" id="navLinks">
        <li><a href="../index.html">Home</a></li>
        <li><a href="../about.html">About</a></li>
        <li><a href="index.html">Blog</a></li>
        <li><a href="../index.html#tools">Top Tools</a></li>
        <li><a href="../contact.html">Contact</a></li>
        <li><a href="../index.html#tools" class="nav-cta">Get Started Free</a></li>
      </ul>
      <button class="nav-toggle" id="navToggle" aria-label="Toggle menu" aria-expanded="false">
        <span></span><span></span><span></span>
      </button>
    </div>
  </nav>

  <header class="article-header" aria-labelledby="article-heading">
    <div class="article-header-content">
      <nav aria-label="Breadcrumb" style="margin-bottom:24px; font-size:0.85rem; color:var(--text-muted);">
        <a href="../index.html" style="color:var(--text-muted);">Home</a>
        <span style="margin:0 8px;">›</span>
        <a href="index.html" style="color:var(--text-muted);">Blog</a>
        <span style="margin:0 8px;">›</span>
        <span style="color:var(--accent);">{category}</span>
      </nav>
      <span class="blog-tag" style="margin-bottom:20px; display:inline-block;">{category}</span>
      <h1 id="article-heading">{title}</h1>
      <div class="article-meta" style="margin-top:28px;">
        <span>✍️ AIToolsUK Editorial Team</span>
        <span>📅 {display_date}</span>
        <span>⏱️ 6 min read</span>
      </div>
    </div>
  </header>

  <main class="article-body">
{body}
  </main>

  <section style="padding:60px 0 90px; border-top:1px solid var(--border);">
    <div class="container">
      <h2 style="text-align:center; margin-bottom:36px;">Related Articles</h2>
      <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); gap:22px;">
        <a href="best-ai-tools-uk-small-business.html" class="glass-card" style="display:block; text-decoration:none; padding:26px;">
          <span class="blog-tag" style="margin-bottom:12px; display:inline-block;">AI Overview</span>
          <h3 style="color:var(--text); margin-bottom:8px;">Best AI Tools UK 2026</h3>
          <span class="read-more" style="margin-top:12px; display:inline-flex;">Read →</span>
        </a>
        <a href="index.html" class="glass-card" style="display:block; text-decoration:none; padding:26px;">
          <span class="blog-tag" style="margin-bottom:12px; display:inline-block;">All Posts</span>
          <h3 style="color:var(--text); margin-bottom:8px;">Browse All Articles</h3>
          <span class="read-more" style="margin-top:12px; display:inline-flex;">Browse →</span>
        </a>
        <a href="../contact.html" class="glass-card" style="display:block; text-decoration:none; padding:26px;">
          <span class="blog-tag" style="margin-bottom:12px; display:inline-block;">Contact</span>
          <h3 style="color:var(--text); margin-bottom:8px;">Suggest a Tool</h3>
          <span class="read-more" style="margin-top:12px; display:inline-flex;">Contact →</span>
        </a>
      </div>
    </div>
  </section>

  <footer role="contentinfo">
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <a href="../index.html" class="footer-logo">⚡ AIToolsUK</a>
          <p>Independent AI tools reviews for UK small businesses.</p>
        </div>
        <div class="footer-col">
          <h4>Resources</h4>
          <ul>
            <li><a href="index.html">Blog</a></li>
            <li><a href="best-ai-tools-uk-small-business.html">2026 AI Guide</a></li>
            <li><a href="../about.html">About</a></li>
            <li><a href="../contact.html">Contact</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h4>Legal</h4>
          <ul>
            <li><a href="../privacy.html">Privacy Policy</a></li>
            <li><a href="../terms.html">Terms of Use</a></li>
            <li><a href="../terms.html#affiliate">Affiliate Disclosure</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© {year} AIToolsUK. Independent AI reviews for UK small businesses. Affiliate links are disclosed in our <a href="../terms.html#affiliate">Terms</a>.</p>
        <a href="#">Back to top ↑</a>
      </div>
    </div>
  </footer>

  <div class="cookie-banner" id="cookieBanner" role="dialog" aria-label="Cookie consent">
    <div class="cookie-inner">
      <p>🍪 We use cookies to improve your experience. By continuing you agree to our <a href="../privacy.html">Privacy Policy</a>.</p>
      <div class="cookie-actions">
        <button class="btn-cookie-accept" id="cookieAccept">Accept All</button>
        <button class="btn-cookie-reject" id="cookieReject">Decline</button>
      </div>
    </div>
  </div>

  <script>
    const nav = document.getElementById('nav');
    window.addEventListener('scroll', () => {{ nav.classList.toggle('scrolled', window.scrollY > 0); }}, {{ passive: true }});
    const toggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');
    toggle.addEventListener('click', () => {{
      const open = navLinks.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
    }});
    const observer = new IntersectionObserver((entries) => {{
      entries.forEach(e => {{ if (e.isIntersecting) {{ e.target.classList.add('visible'); observer.unobserve(e.target); }} }});
    }}, {{ threshold: 0.1, rootMargin: '0px 0px -48px 0px' }});
    document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
    (function() {{
      var b = document.getElementById('cookieBanner');
      if (!localStorage.getItem('aitoolsuk_consent')) setTimeout(function() {{ b.classList.add('visible'); }}, 1000);
      document.getElementById('cookieAccept').addEventListener('click', function() {{
        localStorage.setItem('aitoolsuk_consent', 'all'); b.classList.remove('visible');
      }});
      document.getElementById('cookieReject').addEventListener('click', function() {{
        localStorage.setItem('aitoolsuk_consent', 'essential'); b.classList.remove('visible');
      }});
    }})();
  </script>
</body>
</html>
"""


def build_page(slug, title, category, body, today):
    iso_date    = today.isoformat()
    display_date = today.strftime("%B %d, %Y")
    year        = today.year
    # Generate a tight meta description from the title
    meta_desc = f"Expert guide for UK small businesses: {title}. Tested and reviewed by the AIToolsUK editorial team in {year}."[:160]

    return PAGE_TEMPLATE.format(
        slug=slug, title=title, category=category, body=body,
        iso_date=iso_date, display_date=display_date, year=year,
        meta_desc=meta_desc, base_url=BASE_URL,
    )


# ---------------------------------------------------------------------------
# blog/index.html updater
# ---------------------------------------------------------------------------

CARD_TEMPLATE = """\

        <a href="{slug}.html" class="blog-card glass-card fade-in" style="padding:0; overflow:hidden; text-decoration:none;">
          <div class="blog-card-thumb" style="background: linear-gradient(135deg, {gradient});">{emoji}</div>
          <div class="blog-card-body">
            <div class="blog-meta"><span class="blog-tag">{category}</span><span>{display_date}</span><span>6 min</span></div>
            <h3>{title}</h3>
            <p>Expert guide for UK small business owners. Practical advice on using this tool to save time and grow in {year}.</p>
            <span class="read-more">Read article →</span>
          </div>
        </a>
"""

def update_blog_index(slug, title, category, emoji, gradient, today):
    with open(INDEX, "r", encoding="utf-8") as f:
        html = f.read()

    card = CARD_TEMPLATE.format(
        slug=slug, title=title, category=category, emoji=emoji,
        gradient=gradient, display_date=today.strftime("%B %Y"),
        year=today.year,
    )

    marker = '<div class="blog-grid">'
    if marker not in html:
        print("WARNING: Could not find blog-grid marker in blog/index.html — insert card manually.")
        return False

    html = html.replace(marker, marker + card, 1)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    return True


# ---------------------------------------------------------------------------
# sitemap.xml updater
# ---------------------------------------------------------------------------

def update_sitemap(slug, today):
    with open(SITEMAP, "r", encoding="utf-8") as f:
        xml = f.read()

    entry = f"""
  <url>
    <loc>{BASE_URL}/blog/{slug}.html</loc>
    <lastmod>{today.isoformat()}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>

"""
    xml = xml.replace("</urlset>", entry + "</urlset>")
    with open(SITEMAP, "w", encoding="utf-8") as f:
        f.write(xml)


# ---------------------------------------------------------------------------
# Git helper
# ---------------------------------------------------------------------------

def git_push(slug):
    cmds = [
        ["git", "-C", SITE_DIR, "add", "."],
        ["git", "-C", SITE_DIR, "commit", "-m", f"Daily post: {slug}"],
        ["git", "-C", SITE_DIR, "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Git error: {result.stderr.strip()}")
            return False
        print(result.stdout.strip())
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    dry_run = "--dry-run" in sys.argv
    do_push = "--push" in sys.argv

    # Pick topic
    slug, title, category, emoji, gradient = pick_topic()
    if not slug:
        print("All topics covered — add more rows to TOPICS to continue.")
        sys.exit(0)

    print(f"Topic  : {title}")
    print(f"Slug   : {slug}")
    print(f"Category: {category}")

    if dry_run:
        print("[dry-run] Exiting without generating.")
        sys.exit(0)

    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in environment or in", ENV_FILE)
        sys.exit(1)

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

    today = datetime.date.today()

    # Generate content
    print("Generating article with Claude...")
    body = generate_body(client, slug, title, category)
    print(f"Generated {len(body.split())} words of HTML body content.")

    # Build full page
    page_html = build_page(slug, title, category, body, today)

    # Save post
    out_path = os.path.join(BLOG_DIR, f"{slug}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page_html)
    print(f"Saved  : blog/{slug}.html")

    # Update blog index
    if update_blog_index(slug, title, category, emoji, gradient, today):
        print("Updated: blog/index.html")

    # Update sitemap
    update_sitemap(slug, today)
    print("Updated: sitemap.xml")

    # Git push
    if do_push:
        print("Pushing to GitHub...")
        if git_push(slug):
            print(f"Live at: {BASE_URL}/blog/{slug}.html")
    else:
        print("\nNext step:")
        print(f"  git -C {SITE_DIR} add . && git -C {SITE_DIR} commit -m 'Daily post: {slug}' && git -C {SITE_DIR} push")


if __name__ == "__main__":
    main()

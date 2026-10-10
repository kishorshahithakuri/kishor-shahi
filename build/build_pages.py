#!/usr/bin/env python3
"""Generate subpages (about-me, projects, case studies, 404) by reusing the
shared chrome extracted from the reconstructed index.html."""
import os, re

H = open("index.html", encoding="utf-8").read()
HEAD_TPL = open("build/head.html").read()

# ---------------------------------------------------------- balanced slicing
from html.parser import HTMLParser
line_starts = [0]
for m in re.finditer(r"\n", H):
    line_starts.append(m.end())
def off(l, c): return line_starts[l - 1] + c

VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr"}

class Ev(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.ev = []
    def handle_starttag(self, tag, attrs):
        l, c = self.getpos(); s = off(l, c)
        self.ev.append(("s", tag, s, H.find(">", s) + 1, dict(attrs)))
    def handle_startendtag(self, tag, attrs):
        l, c = self.getpos(); s = off(l, c)
        self.ev.append(("x", tag, s, H.find("/>", s) + 2, dict(attrs)))
    def handle_endtag(self, tag):
        l, c = self.getpos(); s = off(l, c)
        self.ev.append(("e", tag, s, H.find(">", s) + 1, None))

p = Ev(); p.feed(H)

def find_block(pred):
    idx = next(i for i, e in enumerate(p.ev)
               if e[0] in ("s", "x") and pred(e))
    if p.ev[idx][0] == "x":
        return H[p.ev[idx][2]:p.ev[idx][3]]
    depth, tag = 0, p.ev[idx][1]
    for j in range(idx, len(p.ev)):
        k, t = p.ev[j][0], p.ev[j][1]
        if k == "s" and t == tag and t not in VOID: depth += 1
        elif k == "e" and t == tag:
            depth -= 1
            if depth == 0:
                return H[p.ev[idx][2]:p.ev[j][3]]
    raise RuntimeError("unbalanced")

NAV = find_block(lambda e: e[1] == "div" and "framer-5nx1n6-container" in (e[4].get("class") or ""))
FOOTER = find_block(lambda e: e[1] == "div" and "framer-z6nlpy-container" in (e[4].get("class") or ""))
LOGO = find_block(lambda e: e[1] == "div" and "framer-qu8yxn" in (e[4].get("class") or ""))
SVGTPL = find_block(lambda e: e[1] == "div" and e[4].get("id") == "svg-templates")

# nav active-state fixer
_BORDER_FRAME = ('<div class="framer-bcx4hc" data-border="true" data-framer-name="Border frame" '
                 'style="--border-bottom-width: 1px; --border-color: var(--token-ff14f010-34c5-4ada-b047-4cbbbdde5f72, rgb(255, 255, 255)); '
                 '--border-left-width: 1px; --border-right-width: 1px; --border-style: solid; --border-top-width: 1px; '
                 'mask: linear-gradient(0deg, rgba(0, 0, 0, 0) 59%, rgba(0, 0, 0, 0.4) 92%); border-radius: 8px; opacity: 1;"></div>')

def _to_inactive(block):
    """Normalize any nav anchor to the inactive appearance."""
    block = re.sub(r'\s*data-framer-page-link-current="true"', "", block)
    block = block.replace('data-framer-name="Active"', 'data-framer-name="Inactive"')
    block = block.replace("framer-v-47hvj9", "framer-v-tickgc")
    # drop the border frame if present
    block = re.sub(r'<div class="framer-bcx4hc".*?</div>', "", block, flags=re.S)
    # background -> transparent, no shadow
    block = re.sub(r'style="background-color:\s*var\(--token-9a0d4a11[^;]*;\s*'
                   r'border-radius:\s*8px;\s*box-shadow:\s*rgba\(0,\s*0,\s*0,\s*0\.25\)[^;]*;',
                   'style="background-color: rgba(0, 0, 0, 0); border-radius: 8px; box-shadow: none;',
                   block, count=1)
    # icon tint -> white, icon shape back per original (home icon is house)
    block = re.sub(r'--43q7um:\s*var\(--token-23300cb5[^)]*\)\)',
                   '--43q7um: var(--token-ff14f010-34c5-4ada-b047-4cbbbdde5f72, rgb(255, 255, 255))',
                   block, count=1)
    return block

def _to_active(block):
    block = _to_inactive(block)
    block = block.replace('data-framer-name="Inactive"', 'data-framer-name="Active"')
    block = block.replace("<a ", '<a data-framer-page-link-current="true" ', 1)
    block = block.replace("framer-v-tickgc", "framer-v-47hvj9")
    block = re.sub(r'style="background-color:\s*rgba\(0,\s*0,\s*0,\s*0\);\s*'
                   r'border-radius:\s*8px;\s*box-shadow:\s*none;',
                   'style="background-color: var(--token-9a0d4a11-50be-4427-8bd5-52f24bcd6833, rgb(0, 0, 0)); '
                   'border-radius: 8px; box-shadow: rgba(0, 0, 0, 0.25) 1px 1px 2px 0px;',
                   block, count=1)
    block = re.sub(r'--43q7um:\s*var\(--token-ff14f010[^)]*\)\)',
                   '--43q7um: var(--token-23300cb5-69d3-4523-98ae-aa0396a0f349, rgb(115, 199, 255))',
                   block, count=1)
    # insert border frame after the icon div (first div child)
    block = re.sub(r'(<div class="framer-(?:dcMSq|SwQj8|BRx8O|m5pZK) framer-nn5mc5"[^>]*></div>)',
                   r'\1' + _BORDER_FRAME.replace("\\", "\\\\"), block, count=1)
    return block

def nav_for(path_prefix):
    def is_current(href):
        if href == "/":
            return path_prefix == "/"
        if href.startswith("/projects"):
            return path_prefix.startswith("/projects")
        return href != "/" and path_prefix.startswith(href.rstrip("/"))

    def fix(m):
        block, href = m.group(0), m.group(1)
        return _to_active(block) if is_current(href) else _to_inactive(block)

    return re.sub(r'<a\b[^>]*href="([^"]+)"[^>]*>.*?</a>', fix, NAV, flags=re.S)

# ------------------------------------------------------------------ helpers
def page(title, desc, body_inner, nav, extra_head=""):
    head = HEAD_TPL.replace("<title>Affinitty - Creative portfolio template</title>",
                            f"<title>{title}</title>")
    head = head.replace(
        '<meta name="description" content="Affinitty is a bold, colorful Framer template for product designers and creative studios, featuring expressive layouts, playful interactions, responsive pages and CMS-powered project case studies.">',
        f'<meta name="description" content="{desc}">')
    head = head.replace('<link rel="stylesheet" href="/assets/css/site.css">',
                        '<link rel="stylesheet" href="/assets/css/site.css">\n'
                        '<link rel="stylesheet" href="/assets/css/pages.css">' + extra_head)
    return (head + "<body>\n"
            '<div class="framer-ruT5y framer-1t0l5y4">'
            '<div class="framer-UCx3k framer-nn2BE framer-2QGTM framer-72rtr7">'
            '<main class="framer-1yqc2l0 pg-main">'
            + body_inner +
            "</main>"
            + nav + FOOTER + LOGO +
            "</div><div id=\"template-overlay\"></div></div>\n"
            + SVGTPL +
            '\n<script src="/assets/js/lenis.min.js"></script>\n'
            '<script src="/assets/js/site.js" defer></script>\n'
            "</body>\n</html>\n")

def w(path, html):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    open(path, "w", encoding="utf-8").write(html)
    print("wrote", path, len(html))

CDN = "https://framerusercontent.com/images/"
IMG = {
    "portrait":  CDN + "eOAKY7ihhaAKr8DRF1eXWVNxmCE.png",
    "grain":     CDN + "6mcf62RlDfRfU61Yg5vb2pefpi4.png",
    "deco1":     CDN + "ywHiSyOD6QcOlm3jZgmHZcwnT2Y.png",
    "deco2":     CDN + "oAm6wEPMYbo31e7g9SfKwtNI.png",
    "sig":       CDN + "8yENZgpFTdxiDNo6UIoOG25S27c.png",
    "way":       CDN + "4YVeaODzKIwKxlAr72YQhQFv5M.png",
    "pulse":     CDN + "iiaPdD7C3jqGnJHupoRapTPegvk.png",
    "tex1":      CDN + "PThbyRGjsjFqOgrHW0pM9MFYWg.png",
    "tex2":      CDN + "fUOGkMjpaxheOKBADSKZMeXbCs.png",
    "tex3":      CDN + "cQjRhc5LdTED0OKUohD8ZLRh0w.png",
    "tex4":      CDN + "NDCbcFqm7KpnEDqv5T17cjqzw.png",
    "b1":        CDN + "bMMZH91XfFQP9Y1D3y89NsX1Bc.png",
    "b2":        CDN + "ZMQJ6vG1Sz9r06CEtQSmZ0rbYo0.png",
    "avatar":    CDN + "0igUSIkDwOquXcWtIBmuwwuNMU0.png",
    "logo":      CDN + "3FfAWWGT5XRDJN61180XZDjn7A.png",
    "og":        CDN + "uKkDPQ7WpZUCBkO5CRsAWZf3A8.png",
}

PROJECTS = [
    dict(slug="signalflow-ai-workspace", name="SignalFlow",
         tags=["AI", "Workspace"], date="Jul 18, 2026", img="sig", tagcolor="purple",
         desc="A focused AI operations platform that turns complex automations into workflows teams can understand, supervise, and trust."),
    dict(slug="wayfinder-logistics-command", name="Wayfinder",
         tags=["Logistics", "Command"], date="Mar 14, 2026", img="way", tagcolor="blue",
         desc="A real-time operations center that gives logistics teams one calm view of routes, risks, capacity, and exceptions."),
    dict(slug="pulse-clinical-intelligence", name="Pulse",
         tags=["Clinical", "Intelligence"], date="May 22, 2026", img="pulse", tagcolor="green",
         desc="A clinical decision workspace that helps care teams move from scattered patient signals to clear, accountable next steps."),
]

# ------------------------------------------------------------- project card
def project_card(pr, big=False):
    tagc = {"purple": "var(--token-040d3d86-1538-4ae9-a142-5059428f767b, rgb(132, 39, 222))",
            "blue": "var(--token-1e67be23-8764-44ff-affe-9a6b377702e4, rgb(0, 143, 240))",
            "green": "var(--token-3886f447-d2f4-4544-8901-fa714ec88a15, rgb(3, 151, 84))"}[pr["tagcolor"]]
    tags = "".join(f'<span class="pc-tag" style="background:{tagc}">{t}</span>' for t in pr["tags"])
    return f'''
<a class="pc-card{' pc-big' if big else ''}" href="/projects/{pr["slug"]}/" data-framer-name="Desktop">
  <span class="pc-frame">
    <span class="corner c-tl" style="--cborder:{tagc}"></span><span class="corner c-tr" style="--cborder:{tagc}"></span>
    <span class="corner c-bl" style="--cborder:{tagc}"></span><span class="corner c-br" style="--cborder:{tagc}"></span>
    <span class="pc-meta"><span class="pc-name">{pr["name"]}</span><span class="pc-date">{pr["date"]}</span></span>
    <span class="pc-heading">{' '.join(f'<span>{t}</span>' for t in pr["tags"])}<span>{pr["name"]}</span></span>
    <span class="pc-desc">{pr["desc"]}</span>
    <span class="pc-cta">View case study <span class="pc-arrow">→</span></span>
    <span class="pc-img"><img src="{IMG[pr["img"]]}" alt="{pr["name"]}"><span class="pc-grain" style="background-image:url('{IMG["grain"]}')"></span></span>
    <span class="pc-tags">{tags}</span>
  </span>
</a>'''

# ================================================================ ABOUT ME
about = f'''
<section class="pg-hero" data-framer-name="Hero">
  <div class="frame-hero">
    <span class="corner c-tl" style="--cborder:var(--blue)"></span><span class="corner c-tr" style="--cborder:var(--blue)"></span>
    <span class="corner c-bl" style="--cborder:var(--blue)"></span><span class="corner c-br" style="--cborder:var(--blue)"></span>
    <p class="hero-tag">About me</p>
    <h1 class="hero-h1">Designing with intent,<br>building with care</h1>
    <div class="hero-portrait">
      <img src="{IMG["portrait"]}" alt="David Harley">
      <span class="pc-grain" style="background-image:url('{IMG["grain"]}')"></span>
      <span class="hero-chip"><span class="chip-dot" data-pixel-grid><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></span>Available for work</span>
    </div>
    <div class="hero-copy">
      <p class="hero-p">I'm a product designer and Framer creator with a strong focus on building intuitive, scalable, and user-centered digital experiences.</p>
      <a class="btn-primary" href="mailto:uxridham@gmail.com"><span class="corner c-tl sm"></span><span class="corner c-tr sm"></span><span class="corner c-bl sm"></span><span class="corner c-br sm"></span>Get in touch</a>
    </div>
  </div>
</section>

<section class="pg-section">
  <div class="tag-row"><span class="tag-text">My story</span><span class="tag-line"></span>
    <span class="corner c-tl" style="--cborder:var(--green)"></span><span class="corner c-tr" style="--cborder:var(--green)"></span>
    <span class="corner c-bl" style="--cborder:var(--green)"></span><span class="corner c-br" style="--cborder:var(--green)"></span>
  </div>
  <div class="about-cols">
    <p class="about-lead">I deeply care about polish, craft and interfaces that make people feel something. For the past 8 years I've helped startups and studios turn fuzzy ideas into products people actually enjoy using.</p>
    <div class="about-body">
      <p>My path started in visual design, but I quickly fell in love with the logic behind great interfaces — the systems, the states, the tiny transitions that make software feel alive. Today I work across the whole product surface: research, flows, design systems, motion and high-fidelity prototypes in Framer.</p>
      <p>I believe the best digital products are calm, fast and a little bit playful. Every project I take on is an opportunity to prove that complexity doesn't have to feel complicated.</p>
    </div>
  </div>
</section>

<section class="pg-section pg-dark">
  <div class="tag-row light"><span class="tag-text">Experience</span><span class="tag-line"></span>
    <span class="corner c-tl" style="--cborder:var(--purple)"></span><span class="corner c-tr" style="--cborder:var(--purple)"></span>
    <span class="corner c-bl" style="--cborder:var(--purple)"></span><span class="corner c-br" style="--cborder:var(--purple)"></span>
  </div>
  <ul class="xp-list">
    <li><span class="xp-role">Independent Product Designer</span><span class="xp-org">Freelance — worldwide</span><span class="xp-years">2023 — Now</span></li>
    <li><span class="xp-role">Senior Product Designer</span><span class="xp-org">Finova</span><span class="xp-years">2020 — 2023</span></li>
    <li><span class="xp-role">Product Designer</span><span class="xp-org">Northbeam Labs</span><span class="xp-years">2018 — 2020</span></li>
    <li><span class="xp-role">UI Designer</span><span class="xp-org">Studio Mono</span><span class="xp-years">2016 — 2018</span></li>
  </ul>
</section>

<section class="pg-section">
  <div class="tag-row"><span class="tag-text">What I offer</span><span class="tag-line"></span>
    <span class="corner c-tl" style="--cborder:var(--blue)"></span><span class="corner c-tr" style="--cborder:var(--blue)"></span>
    <span class="corner c-bl" style="--cborder:var(--blue)"></span><span class="corner c-br" style="--cborder:var(--blue)"></span>
  </div>
  <div class="skill-grid">
    <div class="skill-card" style="--accent:var(--blue)"><img src="{IMG["tex1"]}" alt=""><h3>Interaction<br>design</h3></div>
    <div class="skill-card" style="--accent:var(--green)"><img src="{IMG["tex2"]}" alt=""><h3>User<br>research</h3></div>
    <div class="skill-card" style="--accent:var(--purple)"><img src="{IMG["tex3"]}" alt=""><h3>AI<br>prototyping</h3></div>
    <div class="skill-card" style="--accent:var(--orange)"><img src="{IMG["tex4"]}" alt=""><h3>Motion<br>design</h3></div>
  </div>
</section>
'''
w("about-me/index.html",
  page("Affinitty - About me", "Meet David Harley — product designer and Framer creator focused on intuitive, scalable, user-centered digital experiences.",
       about, nav_for("/about-me")))

# ================================================================ PROJECTS
cards = "".join(project_card(pr, big=i == 0) for i, pr in enumerate(PROJECTS))
projects_page = f'''
<section class="pg-hero compact">
  <div class="frame-hero">
    <span class="corner c-tl" style="--cborder:var(--purple)"></span><span class="corner c-tr" style="--cborder:var(--purple)"></span>
    <span class="corner c-bl" style="--cborder:var(--purple)"></span><span class="corner c-br" style="--cborder:var(--purple)"></span>
    <p class="hero-tag">Projects</p>
    <h1 class="hero-h1">Work i am proud of</h1>
    <p class="hero-p left">A selection of case studies from the last few years — AI platforms, operations tools and clinical software, each designed to feel simple on the surface and robust underneath.</p>
  </div>
</section>
<section class="pg-section projects-grid">
{cards}
</section>
'''
w("projects/index.html",
  page("Affinitty - Projects", "Selected work by David Harley — AI workspaces, logistics command centers and clinical intelligence tools.",
       projects_page, nav_for("/projects")))

# ========================================================== CASE STUDIES
def case_study(pr, next_pr, overview, challenge, approach, result, imgs):
    tagc = {"purple": "var(--purple)", "blue": "var(--blue)", "green": "var(--green)"}[pr["tagcolor"]]
    tags = "".join(f'<span class="pc-tag" style="background:{tagc}">{t}</span>' for t in pr["tags"])
    return f'''
<section class="pg-hero compact cs-hero">
  <div class="frame-hero">
    <span class="corner c-tl" style="--cborder:{tagc}"></span><span class="corner c-tr" style="--cborder:{tagc}"></span>
    <span class="corner c-bl" style="--cborder:{tagc}"></span><span class="corner c-br" style="--cborder:{tagc}"></span>
    <p class="hero-tag">Case study</p>
    <h1 class="hero-h1">{pr["name"]}</h1>
    <div class="cs-meta">
      <span class="cs-tags">{tags}</span>
      <span class="cs-date">Released {pr["date"]}</span>
    </div>
  </div>
</section>
<section class="pg-section cs-cover">
  <div class="cs-img big"><img src="{IMG[pr["img"]]}" alt="{pr["name"]} interface"><span class="pc-grain" style="background-image:url('{IMG["grain"]}')"></span>
    <span class="corner c-tl" style="--cborder:{tagc}"></span><span class="corner c-tr" style="--cborder:{tagc}"></span>
    <span class="corner c-bl" style="--cborder:{tagc}"></span><span class="corner c-br" style="--cborder:{tagc}"></span>
  </div>
</section>
<section class="pg-section cs-body">
  <div class="cs-grid">
    <div class="cs-side">
      <div class="cs-fact"><span>Role</span><p>Lead product designer</p></div>
      <div class="cs-fact"><span>Timeline</span><p>12 weeks</p></div>
      <div class="cs-fact"><span>Team</span><p>Design + 4 engineers</p></div>
      <div class="cs-fact"><span>Deliverables</span><p>UX flows · Design system · Framer prototype</p></div>
    </div>
    <div class="cs-prose">
      <div class="tag-row"><span class="tag-text">Overview</span><span class="tag-line"></span></div>
      <p class="cs-lead">{overview}</p>
      <div class="tag-row"><span class="tag-text">The challenge</span><span class="tag-line"></span></div>
      <p>{challenge}</p>
      <div class="cs-img"><img src="{imgs[0]}" alt=""><span class="pc-grain" style="background-image:url('{IMG["grain"]}')"></span></div>
      <div class="tag-row"><span class="tag-text">The approach</span><span class="tag-line"></span></div>
      <p>{approach}</p>
      <div class="cs-img"><img src="{imgs[1]}" alt=""><span class="pc-grain" style="background-image:url('{IMG["grain"]}')"></span></div>
      <div class="tag-row"><span class="tag-text">The result</span><span class="tag-line"></span></div>
      <p>{result}</p>
    </div>
  </div>
</section>
<section class="pg-section cs-next">
  <a class="next-link" href="/projects/{next_pr["slug"]}/">
    <span class="next-label">Next project</span>
    <span class="next-name">{next_pr["name"]} <span class="pc-arrow">→</span></span>
  </a>
</section>
'''

CS = {
 "signalflow-ai-workspace": dict(
   overview="SignalFlow asked for a single workspace where operations teams could build, supervise and trust their AI automations. What started as a dashboard brief turned into a full product language for human-in-the-loop AI.",
   challenge="Automation pipelines were powerful but opaque. Teams couldn't tell why a run failed, who approved it, or what would happen next — so they bypassed the tool entirely. The interface had to make machine behaviour legible without dumbing it down.",
   approach="We mapped every automation state with the team, then designed a run timeline that reads like a story: trigger, steps, decisions, outcomes. I prototyped the supervision flow in Framer and tested it with operators weekly, tightening the information hierarchy each round.",
   result="Supervision time dropped by 40%, and teams began shipping automations they previously ran by hand. The design system we built now powers every new SignalFlow surface.",
   imgs=["b1", "tex1"]),
 "wayfinder-logistics-command": dict(
   overview="Wayfinder needed one calm command center for dispatch teams juggling routes, weather, capacity and exceptions across three continents.",
   challenge="Dispatchers were drowning in tabs and radio chatter. Critical exceptions surfaced late, and every tool spoke a different visual language. We needed a single glanceable view that stayed readable at 3am during a storm.",
   approach="I ran ride-alongs with dispatch teams to understand their real prioritisation logic, then designed a layered map view where risk literally rises to the top. High-contrast states, quiet defaults and a strict type scale keep the screen calm under pressure.",
   result="Exception response time fell by half during the first quarter in production, and the command center became the screen the whole operations floor points at.",
   imgs=["b2", "tex2"]),
 "pulse-clinical-intelligence": dict(
   overview="Pulse helps care teams turn scattered patient signals — labs, notes, vitals — into clear, accountable next steps.",
   challenge="Clinical data arrives fragmented and urgent. Existing tools listed signals without context, pushing interpretation burden onto already stretched nurses and physicians. Any mistake in hierarchy could have real consequences.",
   approach="Working closely with clinicians, we designed an evidence-first layout: every recommendation shows its source, confidence and freshness. I built interactive Framer prototypes for ward tablets and validated them in simulated shift handovers.",
   result="Care teams reported higher confidence in triage decisions, and the evidence trail made handovers measurably faster and more accountable.",
   imgs=["b1", "tex3"]),
}

for i, pr in enumerate(PROJECTS):
    nxt = PROJECTS[(i + 1) % len(PROJECTS)]
    body = case_study(pr, nxt, **CS[pr["slug"]])
    w(f"projects/{pr['slug']}/index.html",
      page(f"Affinitty - {pr['name']}", pr["desc"], body, nav_for("/projects")))

# ==================================================================== 404
p404 = '''
<section class="pg-hero compact p404">
  <div class="frame-hero center">
    <span class="corner c-tl" style="--cborder:var(--blue)"></span><span class="corner c-tr" style="--cborder:var(--blue)"></span>
    <span class="corner c-bl" style="--cborder:var(--blue)"></span><span class="corner c-br" style="--cborder:var(--blue)"></span>
    <p class="hero-tag">Error 404</p>
    <h1 class="hero-h1">This page went<br>off the grid</h1>
    <p class="hero-p center">The page you're looking for doesn't exist or has been moved. Let's get you back somewhere nice.</p>
    <a class="btn-primary" href="/"><span class="corner c-tl sm"></span><span class="corner c-tr sm"></span><span class="corner c-bl sm"></span><span class="corner c-br sm"></span>Back to home</a>
  </div>
</section>
'''
w("404.html", page("Affinitty - Page not found", "This page could not be found.", p404, nav_for("/__404")))

print("all pages generated")

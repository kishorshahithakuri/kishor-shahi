#!/usr/bin/env python3
"""Reconstruct index.html from saved sample.html (offset-accurate version)."""
import re
from html.parser import HTMLParser

SRC = "sample.html"
raw = open(SRC, encoding="utf-8").read()

# line-offset index for getpos() -> absolute offset
line_starts = [0]
for m in re.finditer(r"\n", raw):
    line_starts.append(m.end())
def off(line, col):
    return line_starts[line - 1] + col

VOID = {"area","base","br","col","embed","hr","img","input","link","meta",
        "param","source","track","wbr"}

class Ev(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.events = []          # (kind, tag, start, end)
    def handle_starttag(self, tag, attrs):
        l, c = self.getpos(); s = off(l, c)
        end = raw.find(">", s) + 1
        self.events.append(("s", tag, s, end, dict(attrs)))
    def handle_startendtag(self, tag, attrs):
        l, c = self.getpos(); s = off(l, c)
        end = raw.find("/>", s) + 2
        self.events.append(("x", tag, s, end, dict(attrs)))
    def handle_endtag(self, tag):
        l, c = self.getpos(); s = off(l, c)
        end = raw.find(">", s) + 1
        self.events.append(("e", tag, s, end, None))
    def handle_comment(self, data):
        # comments are stripped from the final text instead (regex pass)
        pass
    def handle_decl(self, data): pass
    def handle_pi(self, data): pass

p = Ev(); p.feed(raw)

def find_end(idx):
    """Given index of an opening event, return index+1 of its matching close."""
    kind, tag = p.events[idx][0], p.events[idx][1]
    depth = 0
    for j in range(idx, len(p.events)):
        k, t = p.events[j][0], p.events[j][1]
        if k in ("s",) and t == tag and t not in VOID:
            depth += 1
        elif k == "e" and t == tag:
            depth -= 1
            if depth == 0:
                return j + 1
    return len(p.events)

# locate <div id="main">
main_idx = next(i for i, e in enumerate(p.events)
                if e[0] == "s" and e[1] == "div" and e[4].get("id") == "main")
main_end_idx = find_end(main_idx)
main_start = p.events[main_idx][2]
main_stop = p.events[main_end_idx - 1][3]

# also keep the sibling #svg-templates defs div (icon/cursor SVG definitions)
tpl_idx = next((i for i, e in enumerate(p.events)
                if e[0] == "s" and e[1] == "div"
                and e[4].get("id") == "svg-templates"), None)
tpl_html = ""
if tpl_idx is not None:
    tpl_end = find_end(tpl_idx)
    tpl_html = "\n" + raw[p.events[tpl_idx][2]:p.events[tpl_end - 1][3]]

# collect removal ranges inside main
remove = []
i = main_idx + 1
while i < main_end_idx:
    k, t, s, e, a = p.events[i]
    drop = False
    if k == "s" and t in ("script", "style"):
        j = find_end(i); remove.append((s, p.events[j-1][3])); i = j; continue
    elif k in ("s", "x") and t == "link":
        drop = True
    elif k == "e" and t == "link":
        drop = True
    elif k == "s" and a is not None:
        cls = (a.get("class") or "")
        if ("give-freely-root" in cls or t == "merlin-floating-cta"
                or t == "iframe" or t == "template"):
            j = find_end(i); remove.append((s, p.events[j-1][3])); i = j; continue
    if drop:
        remove.append((s, e))
    i += 1

# build cleaned main text
remove.sort()
out_parts, cur = [], main_start
for s, e in remove:
    if s < cur: continue
    out_parts.append(raw[cur:s]); cur = e
out_parts.append(raw[cur:main_stop])
main = "".join(out_parts)

# strip HTML comments (hydration markers like <!--$--> etc.)
main = re.sub(r"<!--.*?-->", "", main, flags=re.S)

# URL rewriting
main = main.replace("./sample_files/", "https://framerusercontent.com/images/")
SITE = "https://affinitty.framer.website"
main = main.replace(f'href="{SITE}/', 'href="/')
main = main.replace(f'href="{SITE}"', 'href="/"')
main = main.replace('href="https://framer.link/Cisayri"',
                    'href="/resume/David-Harley-Resume.pdf" download')

HEAD = open("build/head.html").read()
TAIL = """
<script src="/assets/js/lenis.min.js"></script>
<script src="/assets/js/site.js" defer></script>
</body>
</html>
"""
open("index.html", "w", encoding="utf-8").write(
    HEAD + "<body>\n" + main + tpl_html + TAIL)
print("written", len(main) + len(tpl_html), "bytes of main+templates")

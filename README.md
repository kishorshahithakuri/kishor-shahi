# Affinitty — Creative Portfolio

A faithful, dependency-light reconstruction of the **Affinitty** creative portfolio
website (affinitty.framer.website), built from the saved homepage snapshot in
`sample.html`.

## Pages

| Route | Description |
|---|---|
| `/` | Home — hero with custom cursor, about letter-reveal, projects, services, testimonials slider |
| `/about-me/` | About page |
| `/projects/` | Projects index |
| `/projects/signalflow-ai-workspace/` | Case study |
| `/projects/wayfinder-logistics-command/` | Case study |
| `/projects/pulse-clinical-intelligence/` | Case study |
| `/resume/David-Harley-Resume.pdf` | Resume download (nav link) |
| `/404.html` | Not-found page |

## Run it

Any static server works:

```bash
python3 -m http.server 8080
```

## Stack

- Static HTML + CSS + vanilla JS (no build step)
- [Lenis](https://github.com/darkroomengineering/lenis) smooth scrolling (vendored, `assets/js/lenis.min.js`)
- Fonts: Inter & Fragment Mono (Google Fonts), PP Neue Montreal (hot-linked from the template's CDN)
- Images are hot-linked from `framerusercontent.com`

## How it was built

- `build/clean_home.py` — reconstructs `index.html` from `sample.html`:
  keeps the original markup/inline styles and saved Framer stylesheet, strips
  editor/browser-extension artifacts, rewrites image URLs and internal links.
- `build/build_pages.py` — generates the subpages, reusing the nav / footer /
  SVG-def blocks extracted from `index.html` (with per-page active nav state).
- `assets/css/framer.css` — the preserved original stylesheet.
- `assets/css/site.css` + `assets/js/site.js` — re-implemented interaction
  layer: appear animations, hero cursor, about-me letter colour reveal,
  testimonial slider (counter / arrows / progress bar), email-copy button,
  animated ribbons, pixel status grid, nav tooltips, page transitions.

Rebuild generated files after editing templates:

```bash
python3 build/clean_home.py
python3 build/build_pages.py
```

## Notes

- The homepage markup, styles and layout come directly from the provided
  `sample.html` snapshot, so desktop rendering matches the original.
- The original subpages were not part of the snapshot; they are original
  implementations that follow the same design system (tokens, frames,
  corner rectangles, typography) with placeholder case-study copy.
- Responsive behaviour below 1200px is handled by the preserved media-query
  rules plus adaptations in `site.css` / `pages.css`.

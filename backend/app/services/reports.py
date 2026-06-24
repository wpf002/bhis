"""
Report rendering: build standalone HTML reports and (optionally) PDFs.

HTML always works. PDF uses WeasyPrint, which is an OPTIONAL dependency carrying
system libraries (pango/cairo). If it is not installed, PDF rendering raises
ReportError so the endpoint can return a clear 501 rather than crashing —
mirroring the email backend's graceful-degradation pattern.

The HTML styling deliberately mirrors the app's "Warm Sanctuary" theme so the
exported report is recognizable as the same product.
"""
import importlib.util
from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List, Optional


class ReportError(RuntimeError):
    pass


def weasyprint_available() -> bool:
    return importlib.util.find_spec("weasyprint") is not None


def render_pdf(html: str) -> bytes:
    if not weasyprint_available():
        raise ReportError("PDF rendering unavailable: install 'weasyprint' (and its system libraries).")
    from weasyprint import HTML  # imported lazily so the dep stays optional
    return HTML(string=html).write_pdf()


# ── Display maps (match the UI) ──────────────────────────────────────────────

_PILLAR_LABELS = {
    "doctrinal_integrity": "Doctrinal Integrity",
    "spiritual_discipline": "Spiritual Discipline",
    "transformation_fruit": "Spiritual Growth",
    "discipleship_depth": "Discipleship Depth",
    "church_health_trust": "Church Health & Trust",
    "engagement_alignment": "Service",
}
_HIDDEN_PILLARS = {"drift_vulnerability"}
_TIER_LABELS = {
    "Spiritually Disengaged": "Spiritually Disengaged",
    "Nominal": "Nominal",
    "Growing": "Growing",
    "Grounded": "Growing",
    "Multiplying Disciple": "Making Disciples",
}
# Warm theme tokens (kept in sync with frontend/tailwind.config.js).
_C = {
    "ink": "#2C2A24",
    "ink_soft": "#6E6658",
    "ink_faint": "#9A917F",
    "canvas": "#F6F1E7",
    "surface": "#FFFFFF",
    "warmth": "#FBF7F0",
    "line": "#E9E1D3",
    "sage": "#4F7355",
    "sage_dark": "#3E5D44",
    "sage_soft": "#E9F0E8",
    "gold": "#C39A4A",
    "gold_dark": "#9A7424",
    "gold_soft": "#F4ECD7",
    "clay": "#BE6E47",
    "clay_dark": "#A85638",
    "clay_soft": "#F6E5DA",
}

# Status → display label, color, and pill background. Mirrors STATUS_TONE in the UI.
_STATUS = {
    "strength":        ("Strong",          _C["sage"],     _C["sage_dark"], _C["sage_soft"]),
    "moderate":        ("Solid",           _C["gold"],     _C["gold_dark"], _C["gold_soft"]),
    "gap":             ("Growing",         _C["clay"],     _C["clay"],      _C["clay_soft"]),
    "significant_gap": ("Needs Attention", _C["clay_dark"], _C["clay_dark"], _C["clay_soft"]),
}


def _status_from_score(score: float) -> str:
    if score >= 70: return "strength"
    if score >= 50: return "moderate"
    if score >= 35: return "gap"
    return "significant_gap"


# ── Shared page shell ────────────────────────────────────────────────────────

_PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Inter', system-ui, sans-serif;
    color: {ink};
    background: {canvas};
    margin: 0;
    line-height: 1.55;
    -webkit-font-smoothing: antialiased;
  }}
  .page {{ max-width: 760px; margin: 0 auto; padding: 48px 40px 80px; }}
  .serif {{ font-family: 'Fraunces', Georgia, serif; font-weight: 500; letter-spacing: -0.01em; }}
  h1, h2, h3 {{ font-family: 'Fraunces', Georgia, serif; font-weight: 500; letter-spacing: -0.01em; margin: 0; }}
  h1 {{ font-size: 30px; }}
  h2 {{ font-size: 20px; }}
  .eyebrow {{ font-size: 11px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: {ink_faint}; }}
  .muted {{ color: {ink_soft}; font-size: 14px; }}
  .card {{ background: {surface}; border: 1px solid {line}; border-radius: 14px; padding: 28px; margin-bottom: 18px; }}

  /* Letterhead */
  .letterhead {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 32px; padding-bottom: 18px; border-bottom: 1px solid {line}; }}
  .brand {{ display: flex; align-items: center; gap: 12px; }}
  .brand .mark {{ width: 40px; height: 40px; border-radius: 12px; background: {sage}; display: inline-flex; align-items: center; justify-content: center; }}
  .brand .name {{ font-family: 'Fraunces', Georgia, serif; font-size: 17px; color: {ink}; line-height: 1; }}
  .brand .tag {{ font-size: 10px; letter-spacing: 0.14em; text-transform: uppercase; color: {ink_faint}; margin-top: 4px; }}
  .meta {{ text-align: right; font-size: 12px; color: {ink_faint}; }}

  /* Hero */
  .hero {{ display: flex; align-items: center; gap: 32px; }}
  .hero .ring {{ width: 132px; height: 132px; flex-shrink: 0; }}
  .hero .ring .num {{ font-family: 'Fraunces', Georgia, serif; font-size: 38px; fill: {ink}; }}
  .hero .ring .of {{ font-size: 9px; letter-spacing: 0.16em; fill: {ink_faint}; }}
  .hero .label {{ font-size: 11px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: {ink_faint}; margin-bottom: 6px; }}
  .hero .tier {{ font-family: 'Fraunces', Georgia, serif; font-size: 28px; color: {ink}; line-height: 1.1; margin-bottom: 8px; }}
  .hero .desc {{ color: {ink_soft}; font-size: 14px; }}

  /* Section */
  .section {{ margin-top: 36px; }}
  .section-head {{ display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 14px; }}

  /* Pillar bars */
  .pillar {{ margin-bottom: 18px; }}
  .pillar:last-child {{ margin-bottom: 0; }}
  .pillar .row {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }}
  .pillar .name {{ font-size: 14px; color: {ink}; }}
  .pillar .right {{ display: flex; align-items: center; gap: 10px; }}
  .pillar .pill {{ font-size: 11px; font-weight: 500; padding: 2px 9px; border-radius: 999px; border: 1px solid transparent; }}
  .pillar .score {{ font-size: 15px; font-weight: 600; color: {ink}; min-width: 28px; text-align: right; }}
  .bar {{ height: 8px; background: {warmth}; border-radius: 999px; overflow: hidden; }}
  .bar .fill {{ height: 100%; border-radius: 999px; }}

  /* Maturity rows (same bar style, no pill) */
  .tier-row {{ margin-bottom: 14px; }}
  .tier-row:last-child {{ margin-bottom: 0; }}
  .tier-row .row {{ display: flex; justify-content: space-between; margin-bottom: 4px; font-size: 13px; }}
  .tier-row .name {{ color: {ink_soft}; }}
  .tier-row .pct {{ color: {ink}; font-weight: 600; }}

  /* Recommendation cards */
  .rec {{ background: {warmth}; border: 1px solid {line}; border-radius: 12px; padding: 20px 22px; margin-bottom: 14px; page-break-inside: avoid; }}
  .rec:last-child {{ margin-bottom: 0; }}
  .rec .title {{ font-family: 'Fraunces', Georgia, serif; font-size: 17px; color: {ink}; margin-bottom: 6px; }}
  .rec .meta {{ font-size: 12px; color: {ink_faint}; margin-bottom: 12px; }}
  .rec p {{ margin: 8px 0; font-size: 14px; color: {ink_soft}; }}
  .rec .scripture {{ background: {gold_soft}; border-radius: 10px; padding: 12px 14px; margin: 12px 0; }}
  .rec .scripture .lbl {{ font-size: 10px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: {gold_dark}; margin-bottom: 4px; }}
  .rec .scripture .text {{ font-family: 'Fraunces', Georgia, serif; font-style: italic; font-size: 14px; color: {ink}; }}
  .rec .when {{ font-size: 11px; color: {ink_faint}; margin-top: 10px; }}

  /* Warning */
  .warn {{ background: {gold_soft}; border: 1px solid {gold}; border-radius: 12px; padding: 16px 20px; margin-top: 20px; }}
  .warn .lbl {{ font-size: 13px; font-weight: 600; color: {gold_dark}; margin-bottom: 4px; }}
  .warn p {{ margin: 0; font-size: 14px; color: {ink_soft}; }}

  .footer {{ margin-top: 48px; padding-top: 20px; border-top: 1px solid {line}; font-size: 12px; color: {ink_faint}; text-align: center; }}

  @media print {{
    body {{ background: white; }}
    .page {{ padding: 24px 28px 32px; }}
    .card, .rec {{ break-inside: avoid; }}
  }}
</style>
</head><body><div class="page">{body}</div></body></html>"""


# ── Building blocks ──────────────────────────────────────────────────────────

def _letterhead(subtitle: str, meta_right: str) -> str:
    sprout = (
        '<svg width="22" height="22" viewBox="0 0 24 24" fill="none">'
        '<path d="M12 21V11" stroke="#F6F1E7" stroke-width="1.8" stroke-linecap="round"/>'
        '<path d="M12 12C12 8.5 9 6.5 5.5 6.5C5.5 10 8 12 12 12Z" fill="#F6F1E7"/>'
        '<path d="M12 10.5C12 7.5 14.5 5 18 5C18 8.2 15.5 10.5 12 10.5Z" fill="#CFE0CC"/>'
        '</svg>'
    )
    return (
        '<div class="letterhead">'
        '<div class="brand">'
        f'<span class="mark">{sprout}</span>'
        '<div>'
        f'<div class="name">{escape(subtitle)}</div>'
        '<div class="tag">Biblical Health Intelligence</div>'
        '</div></div>'
        f'<div class="meta">{meta_right}</div>'
        '</div>'
    )


def _score_ring(score: float) -> str:
    """Inline SVG matching the ScoreRing component in the UI (sage→gold gradient)."""
    score = max(0.0, min(100.0, float(score)))
    size, sw = 132, 12
    r = size / 2 - sw
    c = size / 2
    circ = 2 * 3.141592653589793 * r
    filled = (score / 100.0) * circ
    return (
        f'<svg class="ring" viewBox="0 0 {size} {size}" width="{size}" height="{size}">'
        f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="#ECE4D6" stroke-width="{sw}"/>'
        f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="url(#g)" stroke-width="{sw}" '
        f'stroke-dasharray="{filled} {circ}" stroke-linecap="round" transform="rotate(-90 {c} {c})"/>'
        '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        '<stop offset="0%" stop-color="#4F7355"/><stop offset="100%" stop-color="#C39A4A"/>'
        '</linearGradient></defs>'
        f'<text x="{c}" y="{c - 4}" text-anchor="middle" class="num">{round(score)}</text>'
        f'<text x="{c}" y="{c + 14}" text-anchor="middle" class="of">OUT OF 100</text>'
        '</svg>'
    )


def _hero(score: float, tier_display: str, blurb: str) -> str:
    return (
        '<div class="card">'
        '<div class="hero">'
        f'{_score_ring(score)}'
        '<div>'
        '<div class="label">Overall Health</div>'
        f'<div class="tier">{escape(tier_display)}</div>'
        f'<div class="desc">{escape(blurb)}</div>'
        '</div></div></div>'
    )


def _pillar_rows(pillar_scores: Dict[str, Any], pillar_statuses: Optional[Dict[str, Any]] = None) -> str:
    rows = []
    for pillar, score in (pillar_scores or {}).items():
        if pillar in _HIDDEN_PILLARS:
            continue
        label = _PILLAR_LABELS.get(pillar, pillar.replace("_", " ").title())
        score_f = float(score or 0)
        status_key = (pillar_statuses or {}).get(pillar) or _status_from_score(score_f)
        status_label, color, text_color, bg_color = _STATUS.get(status_key, _STATUS["moderate"])
        pct = max(0.0, min(100.0, score_f))
        rows.append(
            '<div class="pillar">'
            '<div class="row">'
            f'<span class="name">{escape(label)}</span>'
            '<span class="right">'
            f'<span class="pill" style="color:{text_color};background:{bg_color};border-color:{text_color}33">{status_label}</span>'
            f'<span class="score">{round(score_f)}</span>'
            '</span></div>'
            f'<div class="bar"><div class="fill" style="width:{pct}%;background:{color}"></div></div>'
            '</div>'
        )
    return "".join(rows)


def _maturity_rows(raw_dist: Dict[str, Any]) -> str:
    merged: Dict[str, float] = {}
    for tier, pct in (raw_dist or {}).items():
        display = _TIER_LABELS.get(tier, tier)
        merged[display] = merged.get(display, 0.0) + float(pct or 0)
    color_for = {
        "Spiritually Disengaged": _C["clay"],
        "Nominal": "#C99A5B",
        "Growing": _C["gold"],
        "Making Disciples": _C["sage"],
    }
    rows = []
    for tier_name, pct in merged.items():
        bar_pct = min(100.0, pct * 2)  # mild visual scaling so small values still show
        rows.append(
            '<div class="tier-row">'
            f'<div class="row"><span class="name">{escape(tier_name)}</span><span class="pct">{round(pct, 1)}%</span></div>'
            f'<div class="bar"><div class="fill" style="width:{bar_pct}%;background:{color_for.get(tier_name, _C["ink_faint"])}"></div></div>'
            '</div>'
        )
    return "".join(rows)


def _recommendations(recs: List[Dict[str, Any]]) -> str:
    if not recs:
        return '<div class="muted">No priority areas right now. Keep doing what you’re doing.</div>'
    blocks = []
    for r in recs:
        pillar = r.get("pillar", "")
        pillar_label = _PILLAR_LABELS.get(pillar, str(pillar).replace("_", " ").title())
        timeline = r.get("timeline", "")
        anchor = r.get("biblical_anchor") or ""
        diagnosis = r.get("diagnosis") or ""
        intervention = r.get("intervention") or ""
        scripture_block = (
            f'<div class="scripture"><div class="lbl">Scripture</div>'
            f'<div class="text">{escape(anchor)}</div></div>'
        ) if anchor else ""
        blocks.append(
            '<div class="rec">'
            f'<div class="title">{escape(str(r.get("title", "")))}</div>'
            f'<div class="meta">{escape(pillar_label)}</div>'
            f'<p>{escape(diagnosis)}</p>'
            f'{scripture_block}'
            f'<p>{escape(intervention)}</p>'
            + (f'<div class="when">Check back in {escape(timeline)}</div>' if timeline else "")
            + '</div>'
        )
    return "".join(blocks)


_TIER_BLURB = {
    "Spiritually Disengaged": "A good place to start. Small, regular steps add up.",
    "Nominal": "There’s a foundation here. A bit more consistency can take you further.",
    "Growing": "Growing well. Stay with the practices that are stretching your people.",
    "Making Disciples": "Bearing fruit and helping others do the same.",
}


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%B %d, %Y")


# ── Public renderers ─────────────────────────────────────────────────────────

def render_individual_html(data: Dict[str, Any]) -> str:
    composite = float(data.get("composite_score") or 0)
    tier = data.get("maturity_tier", "")
    tier_display = _TIER_LABELS.get(tier, tier)
    blurb = _TIER_BLURB.get(tier_display, "")

    warn = ""
    if data.get("credibility_warning"):
        warn = (
            '<div class="warn">'
            '<div class="lbl">Something to consider</div>'
            '<p>A few of your answers point in different directions, which is true for most of us. '
            'Take it as a prompt to reflect, not a verdict.</p>'
            '</div>'
        )

    body = (
        _letterhead("Personal Reflection", _today())
        + _hero(composite, tier_display, blurb)
        + warn
        + '<div class="section"><div class="section-head"><h2>The Six Areas</h2></div>'
          '<div class="card">' + _pillar_rows(data.get("pillar_scores", {}), data.get("pillar_statuses", {})) + '</div></div>'
        + '<div class="section"><div class="section-head"><h2>Where to Focus</h2></div>'
          + _recommendations(data.get("recommendations", []))
          + '</div>'
        + '<div class="footer">Your answers are kept private. This reflection is for your encouragement, not judgment.</div>'
    )
    return _PAGE.format(title="BHIS · Your Results", body=body, **_C)


def render_church_html(data: Dict[str, Any]) -> str:
    composite = float(data.get("health_score") or 0)
    if composite >= 81: tier_display = "Making Disciples"
    elif composite >= 41: tier_display = "Growing"
    elif composite >= 21: tier_display = "Nominal"
    else: tier_display = "Disengaged"
    blurb = _TIER_BLURB.get(tier_display, "")
    respondents = data.get("respondent_count", 0)
    meta_right = (
        f'<div>{_today()}</div>'
        f'<div>{respondents} {"response" if respondents == 1 else "responses"}</div>'
    )

    body = (
        _letterhead("Church Health Report", meta_right)
        + _hero(composite, tier_display, blurb)
        + '<div class="section"><div class="section-head"><h2>The Six Areas</h2></div>'
          '<div class="card">' + _pillar_rows(data.get("pillar_scores", {})) + '</div></div>'
        + '<div class="section"><div class="section-head"><h2>Spiritual Maturity</h2></div>'
          '<div class="card">' + _maturity_rows(data.get("maturity_distribution", {})) + '</div></div>'
        + '<div class="section"><div class="section-head"><h2>Where to Focus</h2></div>'
          + _recommendations(data.get("recommendations", []))
          + '</div>'
        + '<div class="footer">Individual responses are private. Only aggregate results are shown.</div>'
    )
    return _PAGE.format(title="BHIS · Church Health Report", body=body, **_C)

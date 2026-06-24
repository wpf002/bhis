"""
Report rendering: build standalone HTML reports and (optionally) PDFs.

HTML always works. PDF uses WeasyPrint, which is an OPTIONAL dependency carrying
system libraries (pango/cairo). If it is not installed, PDF rendering raises
ReportError so the endpoint can return a clear 501 rather than crashing —
mirroring the email backend's graceful-degradation pattern.
"""
import importlib.util
from html import escape
from typing import Any, Dict, List


class ReportError(RuntimeError):
    pass


def weasyprint_available() -> bool:
    return importlib.util.find_spec("weasyprint") is not None


def render_pdf(html: str) -> bytes:
    if not weasyprint_available():
        raise ReportError("PDF rendering unavailable: install 'weasyprint' (and its system libraries).")
    from weasyprint import HTML  # imported lazily so the dep stays optional
    return HTML(string=html).write_pdf()


# ── HTML building blocks ──────────────────────────────────────────────────────

_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
  body {{ font-family: system-ui, sans-serif; color: #1a1a1a; margin: 40px; line-height: 1.5; }}
  h1 {{ font-size: 26px; margin-bottom: 4px; }}
  h2 {{ font-size: 18px; margin-top: 28px; border-bottom: 1px solid #ddd; padding-bottom: 4px; }}
  .score {{ font-size: 44px; font-weight: 700; color: #2b6cb0; }}
  .muted {{ color: #666; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 8px; }}
  td, th {{ text-align: left; padding: 6px 10px; border-bottom: 1px solid #eee; }}
  .rec {{ margin: 10px 0; padding: 10px 14px; background: #f7fafc; border-left: 3px solid #2b6cb0; }}
  .warn {{ background: #fffaf0; border-left-color: #dd6b20; }}
</style></head><body>{body}</body></html>"""


# Friendly labels for pillars — must match what the UI shows. Keys here are the
# canonical pillar keys used by the scoring engine.
_PILLAR_LABELS = {
    "doctrinal_integrity": "Doctrinal Integrity",
    "spiritual_discipline": "Spiritual Discipline",
    "transformation_fruit": "Spiritual Growth",
    "discipleship_depth": "Discipleship Depth",
    "church_health_trust": "Church Health & Trust",
    "engagement_alignment": "Service",
}
# Drift is computed internally but never shown to the user.
_HIDDEN_PILLARS = {"drift_vulnerability"}
# Tier display labels (Grounded is merged into Growing in the UI).
_TIER_LABELS = {
    "Spiritually Disengaged": "Spiritually Disengaged",
    "Nominal": "Nominal",
    "Growing": "Growing",
    "Grounded": "Growing",
    "Multiplying Disciple": "Making Disciples",
}


def _pillar_table(pillar_scores: Dict[str, Any], pillar_statuses: Dict[str, Any] = None) -> str:
    rows = []
    for pillar, score in (pillar_scores or {}).items():
        if pillar in _HIDDEN_PILLARS:
            continue
        label = _PILLAR_LABELS.get(pillar, pillar.replace("_", " ").title())
        status = (pillar_statuses or {}).get(pillar, "")
        rows.append(f"<tr><td>{escape(label)}</td><td>{score}</td><td class='muted'>{escape(str(status))}</td></tr>")
    return "<table><tr><th>Area</th><th>Score</th><th>Status</th></tr>" + "".join(rows) + "</table>"


def _recommendations(recs: List[Dict[str, Any]]) -> str:
    if not recs:
        return "<p class='muted'>No specific recommendations at this time.</p>"
    blocks = []
    for r in recs:
        anchor = r.get("biblical_anchor") or ""
        blocks.append(
            f"<div class='rec'><strong>{escape(str(r.get('title', '')))}</strong>"
            f"<div class='muted'>{escape(str(r.get('pillar', '')))} · {escape(str(r.get('urgency', '')))}</div>"
            f"<p>{escape(str(r.get('diagnosis', '')))}</p>"
            f"<p>{escape(str(r.get('intervention', '')))}</p>"
            + (f"<p class='muted'>Scripture: {escape(str(anchor))}</p>" if anchor else "")
            + "</div>"
        )
    return "".join(blocks)


def render_individual_html(data: Dict[str, Any]) -> str:
    warn = ""
    if data.get("credibility_warning"):
        warn = ("<div class='rec warn'>A few of your answers point in different directions, "
                "which is true for most of us. Take it as a prompt to reflect, not a verdict.</div>")
    tier = data.get("maturity_tier", "")
    tier_display = _TIER_LABELS.get(tier, tier)
    body = (
        f"<h1>Your Results</h1>"
        f"<p class='muted'>{escape(tier_display)}</p>"
        f"<div class='score'>{data.get('composite_score', 0)}</div>"
        f"{warn}"
        f"<h2>The Six Areas</h2>{_pillar_table(data.get('pillar_scores', {}), data.get('pillar_statuses', {}))}"
        f"<h2>Where to Focus</h2>{_recommendations(data.get('recommendations', []))}"
    )
    return _PAGE.format(title="BHIS Individual Report", body=body)


def render_church_html(data: Dict[str, Any]) -> str:
    raw_dist = data.get("maturity_distribution") or {}
    # Merge Grounded into Growing to match the UI's 4-tier display.
    merged_dist: Dict[str, float] = {}
    for tier, pct in raw_dist.items():
        display = _TIER_LABELS.get(tier, tier)
        merged_dist[display] = merged_dist.get(display, 0.0) + float(pct)
    dist_rows = "".join(
        f"<tr><td>{escape(k)}</td><td>{round(v, 1)}%</td></tr>" for k, v in merged_dist.items()
    )
    body = (
        f"<h1>Church Health Report</h1>"
        f"<p class='muted'>Responses: {data.get('respondent_count', 0)}</p>"
        f"<div class='score'>{data.get('health_score', 0)}</div>"
        f"<h2>The Six Areas</h2>{_pillar_table(data.get('pillar_scores', {}))}"
        f"<h2>Spiritual Maturity</h2><table><tr><th>Tier</th><th>Share</th></tr>{dist_rows}</table>"
        f"<h2>Where to Focus</h2>{_recommendations(data.get('recommendations', []))}"
    )
    return _PAGE.format(title="BHIS Church Report", body=body)

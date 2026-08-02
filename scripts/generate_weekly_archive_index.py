#!/usr/bin/env python3
"""Build bilingual indexes for verified Weekly USD Impact archives."""

from __future__ import annotations

import argparse
import html
import json
import math
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


SPANISH_MONTHS = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

REGIME_ES = {
    "Strong dollar regime": "Régimen fuerte del dólar",
    "Firm dollar regime": "Régimen firme del dólar",
    "Neutral / transitional": "Neutral / transicional",
    "Soft dollar regime": "Régimen suave del dólar",
    "Weak dollar regime": "Régimen débil del dólar",
}


@dataclass(frozen=True)
class ArchiveEdition:
    week: date
    score: float
    regime: str


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def discover_editions(root: Path) -> list[ArchiveEdition]:
    latest_payload = load_json(root / "public/data/usd_impact_score_v2.json")
    current_week = str((latest_payload.get("metadata") or {}).get("latest_date", ""))
    archive_root = root / "public/archive"
    editions: list[ArchiveEdition] = []

    if not archive_root.is_dir():
        return editions

    for directory in archive_root.iterdir():
        if not directory.is_dir() or directory.name == current_week:
            continue

        try:
            week = datetime.strptime(directory.name, "%Y-%m-%d").date()
            payload = load_json(directory / "score.json")
            metadata = payload.get("metadata") or {}
            score = float(metadata.get("latest_score"))
            regime = str(metadata.get("latest_regime", ""))
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            continue

        if metadata.get("latest_date") != directory.name:
            continue
        if not math.isfinite(score) or not regime:
            continue
        if not (directory / "en.html").is_file() or not (directory / "es.html").is_file():
            continue

        editions.append(ArchiveEdition(week=week, score=score, regime=regime))

    return sorted(editions, key=lambda edition: edition.week, reverse=True)


def format_date(value: date, lang: str) -> str:
    if lang == "es":
        return f"{value.day} de {SPANISH_MONTHS[value.month - 1]} de {value.year}"
    return value.strftime("%B %d, %Y").replace(" 0", " ")


def render_index(editions: list[ArchiveEdition], lang: str) -> str:
    if lang == "es":
        page_title = "Semanas anteriores | USD Impact Score"
        eyebrow = "Archivo semanal"
        heading = "Semanas anteriores"
        intro = "Abra una edición semanal verificada para revisar la lectura, el régimen y el comentario publicados en esa fecha."
        empty = "Todavía no hay ediciones semanales anteriores verificadas."
        score_label = "Puntuación"
        link_label = "Abrir edición"
    else:
        page_title = "Previous weeks | USD Impact Score"
        eyebrow = "Weekly archive"
        heading = "Previous weeks"
        intro = "Open a verified weekly edition to review the reading, regime, and commentary published for that date."
        empty = "No previous verified weekly editions are available yet."
        score_label = "Score"
        link_label = "Open edition"

    cards = []
    for edition in editions:
        week = edition.week.isoformat()
        regime = REGIME_ES.get(edition.regime, edition.regime) if lang == "es" else edition.regime
        score = f"{edition.score:+.2f}".replace("-", "−")
        cards.append(
            "<li>"
            f'<a href="/archive/{week}/{lang}.html" target="_blank" rel="noreferrer">'
            f'<time datetime="{week}">{html.escape(format_date(edition.week, lang))}</time>'
            f'<strong>{html.escape(regime)}</strong>'
            f'<span>{score_label}: {score}</span>'
            f'<small>{link_label} →</small>'
            "</a>"
            "</li>"
        )

    archive_content = (
        f'<ul class="archive-list">{"".join(cards)}</ul>'
        if cards
        else f'<p class="empty">{empty}</p>'
    )

    return f"""<!doctype html>
<html lang="{lang}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{page_title}</title>
  <style>
    :root {{ --navy: #071A33; --slate: #5A6472; --gold: #8A6518; --white: #FFFFFF; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; padding: 24px; background: #f7f8fa; color: #161A1F; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; line-height: 1.5; }}
    main {{ max-width: 1060px; margin: 0 auto; }}
    .eyebrow {{ color: var(--gold); font-size: 12px; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; }}
    h1 {{ margin: 6px 0 8px; color: var(--navy); font-size: clamp(28px, 4vw, 40px); line-height: 1.15; }}
    .intro {{ max-width: 780px; margin: 0 0 22px; color: var(--slate); }}
    .archive-list {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; margin: 0; padding: 0; list-style: none; }}
    .archive-list a {{ display: grid; grid-template-columns: minmax(140px, .8fr) minmax(180px, 1fr); gap: 5px 18px; height: 100%; padding: 16px 18px; border: 1px solid #e1e5ea; border-radius: 14px; background: var(--white); color: var(--navy); text-decoration: none; }}
    .archive-list a:hover, .archive-list a:focus-visible {{ border-color: #C9A35B; box-shadow: 0 10px 24px rgba(2,10,20,.08); outline: none; }}
    time {{ color: var(--gold); font-size: 13px; font-weight: 800; }}
    strong {{ line-height: 1.3; }}
    span {{ color: var(--slate); font-size: 14px; }}
    small {{ color: var(--navy); font-weight: 800; text-align: right; }}
    .empty {{ padding: 20px; border: 1px solid #e1e5ea; border-radius: 14px; background: var(--white); color: var(--slate); }}
    @media (max-width: 720px) {{
      body {{ padding: 18px; }}
      .archive-list {{ grid-template-columns: 1fr; }}
      .archive-list a {{ grid-template-columns: 1fr; }}
      small {{ text-align: left; }}
    }}
  </style>
</head>
<body>
  <main>
    <div class="eyebrow">{eyebrow}</div>
    <h1>{heading}</h1>
    <p class="intro">{intro}</p>
    {archive_content}
  </main>
</body>
</html>
"""


def generate_archive_indexes(root: Path) -> list[ArchiveEdition]:
    editions = discover_editions(root)
    archive_root = root / "public/archive"
    for lang in ("en", "es"):
        output = archive_root / lang / "index.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(render_index(editions, lang), encoding="utf-8")
    return editions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    editions = generate_archive_indexes(args.root.resolve())
    print(f"Generated bilingual archive indexes with {len(editions)} previous editions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

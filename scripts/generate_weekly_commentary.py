#!/usr/bin/env python3
"""Generate deterministic weekly commentary from the pipeline score JSON."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

DISPLAY = {
    "DXY": "DXY",
    "WTI": "WTI crude oil",
    "SPX": "S&P 500",
    "VIX": "VIX",
    "BTC": "Bitcoin",
    "GOLD": "gold",
    "UST_2Y": "U.S. 2-year Treasury yield",
    "UST_10Y": "U.S. 10-year Treasury yield",
}

DISPLAY_ES = {
    "DXY": "DXY",
    "WTI": "petróleo WTI",
    "SPX": "S&P 500",
    "VIX": "VIX",
    "BTC": "Bitcoin",
    "GOLD": "oro",
    "UST_2Y": "rendimiento del Tesoro de EE. UU. a 2 años",
    "UST_10Y": "rendimiento del Tesoro de EE. UU. a 10 años",
}

REGIME_ES = {
    "Strong dollar regime": "Régimen de dólar fuerte",
    "Firm dollar regime": "Régimen de dólar firme",
    "Neutral / transitional": "Neutral / transicional",
    "Soft dollar regime": "Régimen de dólar suave",
    "Weak dollar regime": "Régimen de dólar débil",
}


def signed(value: float, digits: int = 2) -> str:
    return f"{value:+.{digits}f}".replace("-", "−")


def nearest_boundary(score: float) -> float:
    return min((-1.0, -0.3, 0.3, 1.0), key=lambda value: abs(score - value))


def load_score(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if len(payload.get("weeks", [])) < 2:
        raise ValueError("Score JSON must contain at least two weekly observations.")
    return payload


def build_context(payload: dict) -> dict:
    metadata = payload["metadata"]
    weeks = payload["weeks"]
    latest = weeks[-1]
    previous = weeks[-2]
    month_ago = weeks[-5] if len(weeks) >= 5 else weeks[0]
    weights = metadata["weights"]

    components = []
    for name, weight in weights.items():
        z_value = float(latest[name])
        contribution = z_value * float(weight)
        components.append({
            "name": name,
            "z": z_value,
            "weight": float(weight),
            "contribution": contribution,
        })
    components.sort(key=lambda item: abs(item["contribution"]), reverse=True)

    score = float(latest["score"])
    return {
        "date": latest["date"],
        "score": score,
        "regime": latest["regime"],
        "previous_regime": previous["regime"],
        "weekly_change": score - float(previous["score"]),
        "four_week_change": score - float(month_ago["score"]),
        "boundary": nearest_boundary(score),
        "components": components,
        "top": components[:3],
        "positive": sum(item["contribution"] > 0 for item in components),
        "negative": sum(item["contribution"] < 0 for item in components),
    }


def driver_lines(context: dict, lang: str) -> str:
    names = DISPLAY_ES if lang == "es" else DISPLAY
    lines = []
    for item in context["top"]:
        direction = "dólar más firme" if item["contribution"] > 0 else "dólar más suave"
        if lang == "en":
            direction = "firmer-dollar" if item["contribution"] > 0 else "softer-dollar"
            lines.append(
                f"- **{names[item['name']]}:** z-score {signed(item['z'])}; "
                f"score contribution {signed(item['contribution'], 3)}, a {direction} contribution."
            )
        else:
            lines.append(
                f"- **{names[item['name']]}:** puntuación z {signed(item['z'])}; "
                f"contribución al índice {signed(item['contribution'], 3)}, coherente con un {direction}."
            )
    return "\n".join(lines)


def render_en(context: dict) -> str:
    date = datetime.strptime(context["date"], "%Y-%m-%d").strftime("%B %-d, %Y")
    regime_note = (
        f"The regime changed from {context['previous_regime']} to {context['regime']}."
        if context["previous_regime"] != context["regime"]
        else f"The regime remains {context['regime']}."
    )
    return f"""# Automated Regime Commentary — Week of {date}

**USD Impact Score: {signed(context['score'])}  |  {context['regime']}**

This commentary is generated automatically from the same weekly score data used by the dashboard. It adds no external market-event claims and makes no forecast.

## What the score is saying

The score is {signed(context['score'])}, with a week-over-week change of {signed(context['weekly_change'])} and a four-week change of {signed(context['four_week_change'])}. {regime_note} Across the eight inputs, {context['positive']} contribute toward a firmer-dollar reading and {context['negative']} toward a softer-dollar reading.

## What is driving the reading

{driver_lines(context, 'en')}

These are the three largest absolute contributions in the current calculation. Each component is standardized and receives the same fixed transmission weight every week.

## What the score is not saying

The framework does not predict next week’s return for the dollar or any component asset. A positive reading describes a cross-asset configuration associated with firmer-dollar transmission; a negative reading describes one associated with softer-dollar transmission. It does not establish timing, causality or a trade.

## What to watch over the coming week

Watch whether the dominant components retain their current standardized positions and whether the reading broadens across more inputs or narrows around one outlier. The nearest regime boundary is {signed(context['boundary'])}. The dashboard label changes only after a completed weekly observation moves through a boundary.

## Methodology reminder

The USD Impact Score combines DXY, WTI, S&P 500, VIX, Bitcoin, gold and the U.S. 2-year and 10-year Treasury yields. Inputs are z-scored against the full sample, clipped at ±3.5 standard deviations and combined with fixed transmission-logic weights. The same calculation is used every week.

---

*Automated Regime Commentary is educational and informational. It is not investment advice, a trading signal or a recommendation to buy or sell any asset. Historical results do not indicate future results.*
"""


def render_es(context: dict) -> str:
    date_obj = datetime.strptime(context["date"], "%Y-%m-%d")
    months = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    date = f"{date_obj.day} de {months[date_obj.month - 1]} de {date_obj.year}"
    regime = REGIME_ES.get(context["regime"], context["regime"])
    previous = REGIME_ES.get(context["previous_regime"], context["previous_regime"])
    regime_note = f"El régimen cambió de {previous} a {regime}." if previous != regime else f"El régimen permanece en {regime}."
    return f"""# Comentario Automático de Régimen — Semana del {date}

**USD Impact Score: {signed(context['score'])}  |  {regime}**

Este comentario se genera automáticamente con los mismos datos semanales que utiliza el panel. No añade afirmaciones sobre eventos externos ni realiza previsiones.

## Qué indica el resultado

El índice se sitúa en {signed(context['score'])}, con un cambio semanal de {signed(context['weekly_change'])} y un cambio de cuatro semanas de {signed(context['four_week_change'])}. {regime_note} Entre las ocho variables, {context['positive']} contribuyen hacia una lectura de dólar más firme y {context['negative']} hacia una lectura de dólar más suave.

## Qué impulsa la lectura

{driver_lines(context, 'es')}

Estas son las tres mayores contribuciones absolutas del cálculo actual. Cada variable se estandariza y recibe el mismo peso fijo de transmisión cada semana.

## Qué no indica el resultado

El marco no pronostica el rendimiento de la próxima semana para el dólar ni para los activos componentes. Una lectura positiva describe una configuración asociada con un dólar más firme y una lectura negativa describe una configuración asociada con un dólar más suave. No establece momento exacto, causalidad ni una operación.

## Qué observar durante la próxima semana

Observe si las variables dominantes mantienen sus posiciones estandarizadas y si la lectura se amplía entre más componentes o se concentra en un solo valor extremo. El límite de régimen más cercano es {signed(context['boundary'])}. La etiqueta del panel cambia únicamente después de una observación semanal completa que atraviese un límite.

## Recordatorio metodológico

El USD Impact Score combina DXY, WTI, S&P 500, VIX, Bitcoin, oro y los rendimientos del Tesoro de EE. UU. a 2 y 10 años. Las variables se estandarizan frente a la muestra completa, se limitan a ±3,5 desviaciones estándar y se combinan con pesos fijos de transmisión. Cada semana se utiliza el mismo cálculo.

---

*El Comentario Automático de Régimen es educativo e informativo. No constituye asesoramiento de inversión, señal de negociación ni recomendación de compra o venta. Los resultados históricos no indican resultados futuros.*
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--score-json", required=True, type=Path)
    parser.add_argument("--commentary-dir", default=Path("commentary"), type=Path)
    parser.add_argument("--bridge-dir", default=Path("data"), type=Path)
    parser.add_argument("--public-data-dir", type=Path)
    args = parser.parse_args()

    payload = load_score(args.score_json)
    context = build_context(payload)
    args.commentary_dir.mkdir(parents=True, exist_ok=True)
    archive = args.commentary_dir / "archive"
    archive.mkdir(parents=True, exist_ok=True)

    english = render_en(context)
    spanish = render_es(context)
    # Keep the original language-neutral path as a synchronized English alias.
    # Older integrations may still read commentary/latest.md directly.
    (args.commentary_dir / "latest.md").write_text(english, encoding="utf-8")
    (args.commentary_dir / "latest_en.md").write_text(english, encoding="utf-8")
    (args.commentary_dir / "latest_es.md").write_text(spanish, encoding="utf-8")
    (archive / f"{context['date']}_en.md").write_text(english, encoding="utf-8")
    (archive / f"{context['date']}_es.md").write_text(spanish, encoding="utf-8")

    bridge = {
        "week_ending": context["date"],
        "score": context["score"],
        "regime": context["regime"],
        "week_over_week_change": context["weekly_change"],
        "four_week_change": context["four_week_change"],
        "nearest_regime_boundary": context["boundary"],
        "drivers": context["components"],
        "generation": {
            "mode": "deterministic",
            "external_model_used": False,
            "external_event_claims_added": False,
        },
    }
    args.bridge_dir.mkdir(parents=True, exist_ok=True)
    bridge_text = json.dumps(bridge, indent=2, ensure_ascii=False)
    (args.bridge_dir / f"weekly_input_{context['date']}.json").write_text(bridge_text, encoding="utf-8")
    if args.public_data_dir:
        args.public_data_dir.mkdir(parents=True, exist_ok=True)
        (args.public_data_dir / "weekly_input_latest.json").write_text(bridge_text, encoding="utf-8")

    print(f"Generated commentary and bridge data for {context['date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

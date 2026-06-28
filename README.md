# IndexRidge Green Planning Intelligence

Public beta MVP for a low-liability UK renewable/planning intelligence product.

## What this is

A public-data monitoring workflow that finds UK planning-application records likely related to solar, battery storage, EV charging, grid/storage, heat pumps, retrofit, and other green-infrastructure themes.

The current public launch is a free validation page only. No paid checkout, ads, newsletter signup, or outreach are active. The first sellable product should be one of:

1. A weekly/monthly paid digest of relevant public planning records.
2. A downloadable monthly CSV data pack.
3. A free sample page used to validate demand before taking payment.

## Low-risk operating rules

- Use public/open data sources only, preferably explicit Open Government Licence sources.
- Do not copy articles, reports, images, maps, proprietary datasets, or paid-platform records into the product.
- Store factual records, short factual summaries, links, and attribution only.
- Do not claim completeness, official status, guaranteed accuracy, investment value, planning advice, legal advice, engineering advice, or regulatory suitability.
- Do not email prospects, launch ads, add analytics/signup forms, or take payment until the user approves the exact copy and platform.
- Keep buyer-facing wording brand-only where practical and avoid personal PII in public materials.

## Current source

The initial MVP uses the official Planning Data platform `planning-application` dataset:

- API: `https://www.planning.data.gov.uk/entity.json?dataset=planning-application&limit=<n>&offset=<n>`
- Dataset metadata: `https://www.planning.data.gov.uk/dataset/planning-application.json`
- Licence: Open Government Licence v3.0
- Attribution: `© Crown copyright and database right 2026`

This source is useful for a low-risk sample, but it is not enough to claim full UK coverage or commercial-grade lead completeness.

## Run

```bash
cd /Users/ahmirarif/Developer/IndexRidgeGreenPlanning
python3 scripts/fetch_green_planning_sample.py --limit 500 --max-pages 3
```

Outputs are written to `outputs/`:

- `green_planning_sample.csv`
- `green_planning_sample.json`
- `green_planning_sample.md`
- `source_licences.json`

For GitHub Pages, copy reviewed public sample outputs into `sample/` so the live page can link to them.

## Verification

```bash
python3 scripts/fetch_green_planning_sample.py --limit 100 --max-pages 1
python3 - <<'PY'
from pathlib import Path
for p in Path('outputs').glob('*'):
    print(p, p.stat().st_size)
PY
```

## Commercial next step

Before paid launch, prepare:

- A payment/checkout page with the exact disclaimers from `LEGAL_RISK_POLICY.md`.
- A non-public sample digest for review.
- A source register showing every data source, licence, attribution, refresh method, and terms-of-use status.
- A user-approved payment platform such as Gumroad/Payhip/Stripe.

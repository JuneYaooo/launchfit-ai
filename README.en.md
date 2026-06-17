<div align="center">

# LaunchFit AI

**Find the right local benchmarks, then check launch risks before your cross-border product goes live.**

[中文](./README.md)

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![Hackathon](https://img.shields.io/badge/International%20Food%20Expo%20Hackathon-2nd%20Place-gold.svg)](#)

2nd place project at an International Food Expo hackathon, now open sourced.

</div>

---

The expensive mistake in cross-border commerce is often not choosing the wrong product. It is **stocking the product first, then discovering that the marketplace needs more documents, the authorization does not cover the channel, the label must be reprinted, or the category cannot be sold**.

LaunchFit AI turns "Can my product go overseas?" into a practical AI checkup report. Give it a product, target market, marketplace, packaging label, certificate report, brand document, or a few local benchmark screenshots. It first shows how similar products in the target market sell, package, price, and build trust; then it tells you what can move forward, what needs remediation, where margin may disappear, and what should stop for human review.

## What Runs Locally Today

This repo now includes a dependency-free lightweight Skill execution layer. Start with a benchmark worksheet, then put product scope, origin country, one or more destination markets, extracted document fields, packaging copy, benchmark rows, and logistics rows into a case bundle to generate both a structured JSON checkup report and a Markdown memo.

```bash
python3 scripts/qualification_audit_schema.py benchmark-validate examples/benchmark-worksheet.json
python3 scripts/qualification_audit_schema.py benchmark-summarize examples/benchmark-worksheet.json

python3 scripts/qualification_audit_schema.py bundle-validate examples/offline-launch-case.json

python3 scripts/qualification_audit_schema.py launch-report \
  examples/offline-launch-case.json \
  > /tmp/launchfit-offline-report.json

python3 scripts/qualification_audit_schema.py validate /tmp/launchfit-offline-report.json

python3 scripts/qualification_audit_schema.py launch-report-markdown \
  /tmp/launchfit-offline-report.json \
  > /tmp/launchfit-offline-report.md
```

The local execution layer covers the core report surfaces promised below: target-market benchmarks, prices and unit prices, packaging and claim risk, logistics route risk, platform admission gaps, expired or mismatched materials, remediation wording, and audit records. More importantly, it splits the review by origin country and destination markets, then generates the best information channels and verification tasks for each market: platform policy, regulator, customs/import, brand/IP, company registry, certification/lab, standards, logistics/warehouse, and origin/export controls.

Benchmarking is the core workflow: worksheets cover direct competitors, substitutes, adjacent references, category leaders, local niche brands, platform best sellers, offline retail shelf products, and DTC/social commerce products. The summary turns those rows into price bands, channel maps, packaging conventions, claims/proof, review signals, and copy / avoid / improve actions.

The boundary is explicit: this repository does not require OCR, live competitor scraping, certificate/trademark/company registry lookups, freight quote APIs, or a review UI. Those capabilities, plus user-provided search channels, platform links, supplier channels, and industry databases, should feed the same `user_search_channels`, `source_candidates`, `research_tasks`, and `external_checks` structures. User-provided screenshots, certificates, and quotes are labeled T4 / `user_provided`; anything that needs official or current-source confirmation remains `needs_external_verification`.

## Core Problems It Solves

- **Pre-listing uncertainty**: can this product sell on Amazon, TikTok Shop, Shopee, Temu, Lazada, AliExpress, or Tmall Global?
- **Marketplace review blocks**: is the real gap brand authorization, a test report, a label issue, an expired certificate, or a scope mismatch?
- **No local benchmark**: how do similar products in the target market price, package, claim, certify, and sell?
- **Packaging and claims risk**: what needs to change in ingredients, allergens, warnings, marks, responsible party, language, or product claims?
- **Pricing and logistics without evidence**: who are the competitors, where is the price band, and will freight or warehousing destroy margin?
- **Inconsistent team review**: reviewers rely on experience, but supplement requests, evidence records, and audit trails are hard to standardize.

## What The Checkup Report Looks Like

| Report module | What users get |
| --- | --- |
| Launch checkup verdict | go / caution / stop / unknown, so you can decide whether to keep pushing |
| Target-market benchmark | How similar local products handle price, pack size, packaging, claims, channels, certifications, and review signals |
| Listing risk map | Where platform, market, category, brand, label, certificate, and logistics risks sit |
| Qualification gap table | Which document is missing, expired, mismatched, or unverifiable |
| Packaging and label fixes | What to change in front/back label, ingredients, allergens, warnings, marks, language, and claims |
| Price and positioning | Price bands, unit prices, channel tiers, packaging angles, and differentiation opportunities |
| Logistics budget view | Cost, speed, and risk tradeoffs across air, sea, warehouse, and local delivery |
| Remediation wording | Clear requests for suppliers, clients, or service providers |
| Review trail | Decision, evidence, sources, gaps, and next actions for team handoff |

## See The Outputs

### Consumer And Competitor Signals

![Consumer and competitor signals](./assets/demo-consumer-competitor-signals.png)

### Target-Market Benchmark And Channel Insight

![Competitor pricing and channels](./assets/demo-competitor-pricing-channels.png)

### Packaging, Formula And Pricing Suggestions

![Packaging, formula and pricing](./assets/demo-packaging-formula-pricing.png)

### Logistics Comparison And Budget

![Logistics budget comparison](./assets/demo-logistics-budget-eu.png)

### US Retail Shelf Concept

![US retail shelf concept](./assets/demo-retail-shelf-concept.png)

## Who It Is For

- **Cross-border sellers and brands**: know whether the product is worth continuing before sampling, stocking, advertising, or booking inventory.
- **Product and operations teams**: evaluate admission, packaging, logistics, and compliance cost alongside sales potential.
- **Compliance and qualification teams**: turn review judgment into fixed statuses, evidence tables, gap lists, and auditable records.
- **Agencies and service providers**: identify which client materials can be used, which must be reissued, and how to ask clearly.

## Coverage

- Marketplaces: Amazon, TikTok Shop, Shopee, Temu, Lazada, AliExpress, Tmall Global
- Markets and regions: US, EU / EEA, UK, Japan, China import, ASEAN / Southeast Asia
- Categories: food, cosmetics, supplements, electronics, household chemicals

Review routes connect to official or authoritative source entry points such as Amazon Seller Central, TikTok Shop Seller Center, FDA, CBP, European Commission, FCC, CPSC, ASEAN, Singapore HSA, Malaysia NPRA, GOV.UK, MHLW, METI, GACC, SAMR, NMPA, WIPO, EUIPO, and USPTO.

## Why It Is More Than Generic Advice

- It establishes platform, country, category, business model, applicant role, brand/IP, and material scope before judging.
- Applicant-provided files prove submission, not external truth; important facts still need registry, issuer, regulator, or platform verification.
- Every issue is tied to severity, evidence, source, impact, and required action so humans can review it.
- Missing scope, missing evidence, expired materials, out-of-scope authorization, suspected alteration, or conflicting official sources produce remediation, rejection, or human escalation instead of a forced pass.

## How It Decides

![CBEC Product Launch Review project logic diagram](./assets/project-logic-diagram-en.png)

<details>
<summary>Structured Decision Statuses</summary>

| Status | Meaning |
| --- | --- |
| `approve` | Current evidence and verification support moving forward. |
| `conditional_approve` | Can proceed after bounded low/medium fixes are completed. |
| `request_more_info` | Material evidence is missing, unverifiable, or out of scope. |
| `reject` | Confirmed serious non-compliance, prohibited product, unauthorized sale, or unfixable invalid material. |
| `escalate_human` | Suspected fraud, sanctions/export-control concern, sensitive identity issue, legal ambiguity, or conflicting authoritative sources. |
| `not_applicable` | The requested review does not apply to the given platform, market, category, or purpose. |

</details>

## 🙏 Acknowledgements

### Core Contributors

- [刘申奥](https://v.douyin.com/2i9vkcO2jl4/) ![Douyin](https://img.shields.io/badge/Douyin-抖音-000000?logo=tiktok&logoColor=white)
- [光城](https://github.com/light-city) ![GitHub](https://img.shields.io/badge/GitHub-light--city-181717?logo=github&logoColor=white)
- [tobin](https://github.com/TobinZuo) ![GitHub](https://img.shields.io/badge/GitHub-TobinZuo-181717?logo=github&logoColor=white)
- [梁馨匀](https://github.com/halobaby0917-maker) ![GitHub](https://img.shields.io/badge/GitHub-halobaby0917--maker-181717?logo=github&logoColor=white)
- [June](https://github.com/JuneYaooo) ![GitHub](https://img.shields.io/badge/GitHub-JuneYaooo-181717?logo=github&logoColor=white)

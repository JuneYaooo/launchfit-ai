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

LaunchFit AI turns "Can my product go overseas?" into a practical AI checkup report. Give it a product, origin country, one or more destination markets, marketplace, packaging label, certificate report, brand document, or a few local benchmark screenshots. It first shows which official channels, user channels, and benchmark signals should be checked for each destination market; then it tells you what can move forward, what needs remediation, where margin may disappear, and what should stop for human review.

## What You Provide

Minimum inputs:

- **Origin country**: where the product is manufactured, assembled, or exported from.
- **Destination markets**: where you want to sell; multiple countries or regions are supported.
- **Marketplace and category**: for example Amazon US food, Temu EU electronics, or TikTok Shop ASEAN cosmetics.
- **Product details**: name, specification, ingredients/materials, claims, brand, and packaging copy.

If available, add certificates, test reports, brand authorization, packaging images, competitor links/screenshots, logistics quotes, supplier details, marketplace search links, industry databases, or internal review records.

## What It Outputs

- **Per-destination review path**: US, EU, and Japan are not merged into one checklist.
- **Best information channels**: platform policy, regulator, customs/import, brand/IP, company registry, certification/lab, standards, logistics/warehouse, origin/export controls, and user-provided search channels.
- **Actionable research tasks**: what to verify, why it matters, priority, evidence fields, freshness window, and source tier.
- **Target-market benchmarks**: local prices, pack sizes, packaging, claims, channels, certifications, and review signals.
- **Listing risks and qualification gaps**: where platform, market, category, brand, label, certificate, and logistics risks sit.
- **Remediation wording and review trail**: usable with suppliers, clients, service providers, or internal reviewers.

## Why It Is More Than Generic Advice

- It establishes origin country, destination markets, platform, category, business model, applicant role, brand/IP, and material scope before judging.
- It does not pretend offline data knows the latest policy; facts needing current confirmation remain `needs_external_verification`.
- User-provided screenshots, certificates, quotes, platform links, and industry databases feed `user_search_channels`, `source_candidates`, `research_tasks`, or `external_checks`, but are not treated as official truth by default.
- Every issue is tied to severity, evidence, source, impact, and required action so humans can review it.
- Missing scope, missing evidence, expired materials, out-of-scope authorization, suspected alteration, or conflicting official sources produce remediation, rejection, or human escalation instead of a forced pass.

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

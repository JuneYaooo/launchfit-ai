<div align="center">

# LaunchFit AI

**Check whether it can sell, then generate a detailed pre-launch checkup report for your cross-border product.**

[中文](./README.md)

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![Hackathon](https://img.shields.io/badge/International%20Food%20Expo%20Hackathon-2nd%20Place-gold.svg)](#)

2nd place project at an International Food Expo hackathon, now open sourced.

This is an **Agent Skill** for Codex, Claude Code, OpenClaw, Hermes, and other agents that support Skills. After installation, you can ask your agent in natural language to generate a detailed pre-launch checkup report for a cross-border product.

![International Food Expo hackathon 2nd place project photo](./assets/photo.jpg)

</div>

---

The expensive mistake in cross-border commerce is often not choosing the wrong product. It is **stocking the product first, then discovering that the marketplace needs more documents, the authorization does not cover the channel, the label must be reprinted, or the category cannot be sold**.

LaunchFit AI turns "Can my product go overseas?" into a practical detailed checkup report. Give it a product, origin country, one or more destination markets, go-to-market route, marketplace or offline channel, packaging label, certificate report, brand document, or a few local benchmark screenshots. It answers three things at once: **admission checkup** for export, import, marketplace, qualification, label, and logistics blockers; **target-market benchmarking** for how comparable local products price, package, claim, sell, and build trust; and **localization recommendations** for how to adjust packaging, copy, channel, price, fulfillment, and remediation before launch. The report then tells you what can move forward, what needs more evidence, where margin may disappear, and what should stop for human review.

## Who It Is For

- **Cross-border sellers and brands**: know whether the product is worth continuing before sampling, stocking, advertising, or booking inventory.
- **Product and operations teams**: evaluate admission, packaging, logistics, localization, and compliance cost alongside sales potential.
- **Compliance and qualification teams**: turn review judgment into fixed statuses, evidence tables, gap lists, and auditable records.
- **Agencies and service providers**: identify which client materials can be used, which must be reissued, and how to ask clearly.

## What You Provide

Minimum inputs:

- **Origin country**: where the product is manufactured, assembled, or exported from.
- **Destination markets**: where you want to sell; multiple countries or regions are supported.
- **Go-to-market route and category**: cross-border ecommerce, physical export/import distribution, or hybrid; for example Amazon US food, Temu EU electronics, TikTok Shop ASEAN cosmetics, or export to a US importer/distributor.
- **Product details**: name, specification, ingredients/materials, claims, brand, and packaging copy.

If available, add certificates, test reports, brand authorization, packaging images, competitor links/screenshots, logistics quotes, supplier details, marketplace search links, industry databases, or internal review records.

## What You Get

- **Detailed checkup report**: a reviewable full report covering destination markets, go-to-market route, export/import/marketplace admission risks, benchmark samples, localization recommendations, packaging and label issues, qualification gaps, logistics budget, remediation wording, and next actions.
- **Core overview card**: a one-screen decision card distilled from the detailed report, useful for founders, clients, suppliers, operators, and compliance reviewers.

## What The Detailed Checkup Report Outputs

- **Per-destination review path**: US, EU, and Japan are not merged into one checklist.
- **Go-to-market route split**: ecommerce prioritizes platform admission, category gating, listings, and fulfillment; physical trade prioritizes export, import, customs, responsible parties, and distributor/retail channels; hybrid runs both tracks separately.
- **Best information channels**: platform policy, regulator, customs/import, brand/IP, company registry, certification/lab, standards, logistics/warehouse, origin/export controls, and user-provided search channels.
- **Actionable research tasks**: what to verify, why it matters, priority, evidence fields, freshness window, and source tier.
- **Target-market benchmarks**: local prices, pack sizes, packaging, claims, channels, certifications, and review signals.
- **Localization recommendations**: packaging hierarchy, label language, claims wording, channel strategy, price band, fulfillment path, and differentiation opportunities.
- **Listing risks and qualification gaps**: where platform, market, category, brand, label, certificate, and logistics risks sit.
- **Remediation wording and review trail**: usable with suppliers, clients, service providers, or internal reviewers.

## Why It Is More Than Generic Advice

- It establishes origin country, destination markets, go-to-market route, marketplace or offline channel, category, business model, applicant role, brand/IP, and material scope before judging.
- It does not pretend offline data knows the latest policy; facts needing current confirmation remain `needs_external_verification`.
- User-provided screenshots, certificates, quotes, platform links, and industry databases feed `user_search_channels`, `source_candidates`, `research_tasks`, or `external_checks`, but are not treated as official truth by default.
- Every issue is tied to severity, evidence, source, impact, and required action so humans can review it.
- Missing scope, missing evidence, expired materials, out-of-scope authorization, suspected alteration, or conflicting official sources produce remediation, rejection, or human escalation instead of a forced pass.

## Core Problems It Solves

- **Pre-listing uncertainty**: can this product sell on Amazon, TikTok Shop, Shopee, Temu, Lazada, AliExpress, or Tmall Global?
- **Unclear sales route**: is this marketplace ecommerce, traditional export/import distribution, or both?
- **Marketplace review blocks**: is the real gap brand authorization, a test report, a label issue, an expired certificate, or a scope mismatch?
- **No local benchmark**: how do similar products in the target market price, package, claim, certify, and sell?
- **Localization uncertainty**: how should front/back labels, language, pack size, claims, visual hierarchy, trust marks, responsible party, and channel expression adapt to local buyers?
- **Packaging and claims risk**: what needs to change in ingredients, allergens, warnings, marks, responsible party, language, or product claims?
- **Pricing and logistics without evidence**: who are the competitors, where is the price band, and will freight or warehousing destroy margin?
- **Inconsistent team review**: reviewers rely on experience, but supplement requests, evidence records, and audit trails are hard to standardize.

## Installation

Send this prompt to Codex, Claude Code, OpenClaw, Hermes Agent, or another agent that supports Skills:

```text
Install the LaunchFit AI Skill for me:
https://github.com/JuneYaooo/launchfit-ai
```

The agent should clone the repository and place it in its local skills directory. Restart the agent or refresh its skills list after installation.

## How To Use

After installation, talk to your agent naturally. For example:

```text
Use LaunchFit AI to evaluate whether this product can sell on Amazon US:
Origin country: China
Destination market: United States
Go-to-market route: Amazon US cross-border ecommerce
Category: food
Product: chili sauce, with ingredient list and packaging copy
Please generate a detailed checkup report covering admission risks, target-market benchmarks, localization recommendations, packaging and label issues, qualification gaps, and next actions.
```

You can also provide certificates, package photos, competitor screenshots, platform links, logistics quotes, or supplier details. LaunchFit AI treats user-provided material as T4 evidence and marks policy, price, qualification, logistics, and regulatory facts that still need current confirmation as `needs_external_verification`.

## Real Run Example

- Product: Fratelli Mantova Equilibrato Extra Virgin Olive Oil 250ml
- Target: import from Italy to China
- Go-to-market route: `physical_trade`
- Input basis: 3 product photos treated as T4 evidence; the agent also searched public commercial channels and added 10 China-market olive-oil benchmark samples. Benchmarks are used as market signals, not as regulatory, import, or label verification.

Core overview card:

![Mantova olive oil import-to-China core overview card](./examples/real-runs/mantova-olive-oil-china-import/outputs/core-card.png)

**Detailed checkup report:**

- [View detailed checkup report PDF](./examples/real-runs/mantova-olive-oil-china-import/outputs/detailed-report.pdf)

## Coverage

- Marketplaces: Amazon, TikTok Shop, Shopee, Temu, Lazada, AliExpress, Tmall Global
- Markets and regions: US, EU / EEA, UK, Japan, China import, ASEAN / Southeast Asia
- Categories: food, cosmetics, supplements, electronics, household chemicals

Review routes connect to official or authoritative source entry points such as Amazon Seller Central, TikTok Shop Seller Center, FDA, CBP, European Commission, FCC, CPSC, ASEAN, Singapore HSA, Malaysia NPRA, GOV.UK, MHLW, METI, GACC, SAMR, NMPA, WIPO, EUIPO, and USPTO.

## 🙏 Acknowledgements

### Core Contributors

- [刘申奥](https://v.douyin.com/2i9vkcO2jl4/) ![Douyin](https://img.shields.io/badge/Douyin-抖音-000000?logo=tiktok&logoColor=white)
- [光城](https://github.com/light-city) ![GitHub](https://img.shields.io/badge/GitHub-light--city-181717?logo=github&logoColor=white)
- [tobin](https://github.com/TobinZuo) ![GitHub](https://img.shields.io/badge/GitHub-TobinZuo-181717?logo=github&logoColor=white)
- [梁馨匀](https://github.com/halobaby0917-maker) ![GitHub](https://img.shields.io/badge/GitHub-halobaby0917--maker-181717?logo=github&logoColor=white)
- [June](https://github.com/JuneYaooo) ![GitHub](https://img.shields.io/badge/GitHub-JuneYaooo-181717?logo=github&logoColor=white)

### Community

- [LINUX DO — Chinese developer community](https://linux.do/)

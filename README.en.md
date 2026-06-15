<div align="center">

# cbec-qualification-review

**An AI pre-launch checkup for cross-border products: market fit, competitors, pricing, packaging, logistics, marketplace admission, and remediation tasks.**

[中文](./README.md)

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![No dependencies](https://img.shields.io/badge/dependencies-none-green.svg)](./scripts/qualification_audit_schema.py)

</div>

---

Use it with a product idea, target market, marketplace, packaging label, certificate report, or brand document. It helps answer: can this product be sold, is it worth launching, what blocks listing approval, and what must be fixed before submission?

## Questions Every Cross-Border Seller Runs Into

- **Before selecting a product**: is this product better suited for the US, EU, Southeast Asia, or China cross-border route? Are there obvious prohibited-product, certification, labeling, or logistics risks?
- **Before listing**: what does Amazon, TikTok Shop, Shopee, Temu, Lazada, AliExpress, or Tmall Global require for this platform, market, and category?
- **When blocked by review**: if the marketplace asks for qualification documents, authorization, or label changes, what exactly needs to be fixed?
- **When pricing**: who are the competitors, what are the channel price bands, and how should packaging and positioning differentiate?
- **When shipping**: how should air freight, sea freight, rail, overseas warehouse, and local delivery be compared by cost, time, restrictions, and cash tied up?
- **When coordinating teams**: how do you turn product details, certificates, brand materials, missing items, and risk conclusions into an executable report?

## What It Produces

- **Launch feasibility view**: target market, marketplace, category, restricted product risk, certification, label, logistics, and brand/IP blockers.
- **Competitor and channel insight**: competitor products, price bands, retail channels, packaging language, audience, and differentiation angles.
- **Packaging and label suggestions**: front/back label content, claims, warnings, certification marks, localization, and marketplace-ready copy direction.
- **Marketplace admission checklist**: required materials by platform, country/region, and category.
- **Logistics and budget comparison**: cost, timing, cash tied up, category restrictions, warehouse needs, and risk notes.
- **Qualification and certificate review**: business registration, brand authorization, trademark, lab reports, COA, SDS/MSDS, CE, FCC, ISO, HACCP, and related evidence consistency.
- **Remediation wording**: applicant-, supplier-, or service-provider-facing requests for missing, expired, inconsistent, or unverified evidence.

## Common Use Cases

| Scenario | Why It Is Frequent | Typical Output |
| --- | --- | --- |
| New product launch review | Every new listing needs market, platform, and compliance risk checks | Launch feasibility, risks, materials, next actions |
| Marketplace/category review block | Sellers often get stuck on qualification, authorization, or label requests | Gap explanation, supplement list, applicant-facing wording |
| Competitor and pricing refresh | Pricing and positioning change repeatedly | Competitor table, channel price bands, differentiation advice |
| Packaging and label localization | Food, cosmetics, electronics, and household goods often need local packaging changes | Label suggestions, warning/claim/certification checks |
| Logistics route selection | Cost, time, restrictions, and cash tied up directly affect margin | Air/sea/rail/warehouse comparison |
| Internal review SOP | Teams need reusable operating rules and audit trails | Rule matrix, JSON output, audit log, review records |

## Project Logic Diagram

![CBEC Product Launch Review project logic diagram](./assets/project-logic-diagram-en.png)

## Decision Statuses

When a clear decision is needed, the final output uses one fixed status:

| Status | Meaning |
| --- | --- |
| `approve` | Current evidence and verification support moving forward. |
| `conditional_approve` | Can proceed after bounded low/medium fixes are completed. |
| `request_more_info` | Material evidence is missing, unverifiable, or out of scope. |
| `reject` | Confirmed serious non-compliance, prohibited product, unauthorized sale, or unfixable invalid material. |
| `escalate_human` | Suspected fraud, sanctions/export-control concern, sensitive identity issue, legal ambiguity, or conflicting authoritative sources. |
| `not_applicable` | The requested review does not apply to the given platform, market, category, or purpose. |

## Installation

### Codex

```bash
mkdir -p ~/.codex/skills
cp -R /path/to/cbec-qualification-review ~/.codex/skills/cbec-qualification-review
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
cp -R /path/to/cbec-qualification-review ~/.claude/skills/cbec-qualification-review
```

Restart the corresponding agent after installation so the skill metadata reloads.

## Examples

```text
Use cbec-qualification-review to evaluate whether this olive oil product is suitable for Amazon US, including competitors, pricing, packaging, logistics, and listing risks.
```

```text
Use cbec-qualification-review to run a pre-listing check for TikTok Shop Malaysia skincare and list missing materials and label risks.
```

```text
Use cbec-qualification-review to compare air freight, sea freight, and overseas warehouse routes for this product entering the EU.
```

```text
Use cbec-qualification-review to analyze these competitor screenshots and product details, then suggest price band, channels, packaging angles, and launch preparation tasks.
```

```text
Use cbec-qualification-review to turn these business licenses, trademark certificates, COA, SDS, and lab reports into structured review JSON and a supplement request.
```

## Safety And Scope

This project supports cross-border product launch review, marketplace listing preparation, qualification review, material pre-review, remediation drafting, and internal process design. It does not provide legal advice and does not replace final judgment from marketplaces, regulators, certification bodies, or professional compliance advisors.

When documents contain identity records, bank accounts, personal contact details, contracts, business registration numbers, or other sensitive data, follow [`references/privacy-security.md`](./references/privacy-security.md) for minimization, redaction, and audit records.

<div align="center">

# cbec-qualification-review

**An auditable Agent Skill for cross-border e-commerce seller, brand, product, certificate, and marketplace admission review.**

[中文](./README.md)

[![Skill](https://img.shields.io/badge/Agent-Skill-orange.svg)](./SKILL.md)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![No dependencies](https://img.shields.io/badge/dependencies-none-green.svg)](./scripts/qualification_audit_schema.py)

</div>

---

## What It Does

- **Seller and KYB review**: business registration, tax records, payee entity, beneficial owner, store applicant, and service provider qualifications.
- **Brand and IP review**: trademark certificates, authorization letters, distribution agreements, authorization chain, sales territory, platform/channel scope, and validity period.
- **Product and category admission**: food, supplements, cosmetics, electronics, household chemicals, restricted products, and prohibited-product risks.
- **Certificate and report checks**: CE, FCC, COA, SDS/MSDS, ISO, HACCP, Halal, Organic, lab reports, issuer, scope, date, and product match.
- **Platform rule routing**: generate review checklists for Amazon, TikTok Shop, Shopee, Temu, Lazada, AliExpress, Tmall Global, and similar marketplaces.
- **Remediation requests**: convert missing, expired, inconsistent, or unverified evidence into applicant-facing supplement requests.
- **Structured audit output**: fixed JSON contract, evidence table, source tier, risk level, decision status, and audit log.

## Best-Fit Scenarios

| Scenario | Fit | Notes |
| --- | --- | --- |
| Seller onboarding pre-review | Strong | Organizes applicant, platform, market, category, submitted documents, and gaps. |
| Brand authorization review | Strong | Checks grantor authority, grantee, brand, territory, platform, product scope, and validity. |
| Certificate and report form review | Strong | Flags expiry, entity mismatch, model mismatch, unclear issuer, and scope gaps. |
| Marketplace category checklist | Good | Generates an initial checklist from rule packs; final decisions still require official-source verification. |
| Internal review process design | Good | Includes data model, state logic, evidence chain, and supplement request templates. |
| Replacing legal or compliance final advice | Not suitable | This is an operational review framework, not legal advice or a regulator/platform final interpretation. |

## Decision Statuses

The final decision uses one fixed status:

| Status | Meaning |
| --- | --- |
| `approve` | Key requirements are satisfied and no high-risk blocker remains. |
| `conditional_approve` | Only bounded low/medium fixes remain. |
| `request_more_info` | Material evidence is missing, unverifiable, or out of scope. |
| `reject` | Confirmed serious non-compliance, prohibited product, unauthorized sale, or unfixable invalid material. |
| `escalate_human` | Suspected fraud, sanctions/export-control concern, sensitive identity issue, legal ambiguity, or conflicting authoritative sources. |
| `not_applicable` | The requested review does not apply to the given platform, market, category, or purpose. |

## Project Logic Diagram

![CBEC Qualification Review project logic diagram](./assets/project-logic-diagram-en.png)

This diagram explains the full path from submitted materials to rule routing, official-source verification, risk decision, and audit output. The image prompt is available at [`assets/project-logic-diagram-en.image2-prompt.md`](./assets/project-logic-diagram-en.image2-prompt.md).

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
Use cbec-qualification-review to review this Amazon US food category onboarding package and decide whether it can pass.
```

```text
Use cbec-qualification-review to check whether this brand authorization covers TikTok Shop Malaysia and skincare products.
```

```text
Use cbec-qualification-review to design a review checklist for Temu electronics supplier admission.
```

```text
Use cbec-qualification-review to turn these business licenses, trademark certificates, COA, SDS, and lab reports into structured review JSON.
```

```text
Use cbec-qualification-review to draft an applicant-facing supplement request based on the current gaps.
```

## Safety And Scope

This project supports cross-border e-commerce qualification review, material pre-review, remediation drafting, and internal process design. It does not provide legal advice and does not replace final judgment from marketplaces, regulators, certification bodies, or professional compliance advisors.

When documents contain identity records, bank accounts, personal contact details, contracts, business registration numbers, or other sensitive data, follow [`references/privacy-security.md`](./references/privacy-security.md) for minimization, redaction, and audit records.

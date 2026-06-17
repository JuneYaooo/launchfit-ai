# Global Country Framework

This framework makes the skill usable for any destination country or region, even when no mature country-specific rule pack exists.

## Core Principle

Never block usage just because a country rule pack is missing. Use the global baseline workflow:

1. Identify origin country/region, destination country/region, platform, category, business model, and applicant role.
2. Load `data/rulepacks/index.json` and check whether a country/region pack exists.
3. If a mature pack exists, use it as the starting checklist.
4. If no mature pack exists, use `data/rulepacks/global-baseline.json`.
5. Verify current official sources for the exact country/category/platform before a final decision.
6. Record gaps as candidates for a future country rule pack.

## Jurisdiction Layers

For any origin/destination pair, route the review through these layers:

| Layer | What to check |
|---|---|
| Marketplace site | Platform seller eligibility, category gating, restricted product policy |
| Destination country | Import permissions, product safety, labeling, claims, local representative/importer |
| Origin country | Export permissions, certificate of origin, exporter/manufacturer evidence, origin-label consistency |
| Regional bloc | EU/EEA, GCC, ASEAN, Mercosur, EAEU, UK, AU/NZ, or other regional rules where applicable |
| Product regulator | Food, cosmetics, supplements, electronics, chemicals, toys, medical, pesticides, textiles |
| Customs/tax | Importer of record, customs docs, VAT/GST, EORI/IOSS/VAT ID, bonded/direct mail route |
| IP/brand | Trademark territory/class, authorization chain, anti-counterfeit rules |
| Data/privacy | KYC/KYB documents, identity data, local data transfer limits if relevant |

## Fallback Checklist For Any Country

When no specific rule pack exists, start with:

- Seller/entity eligibility for the platform and marketplace site.
- Product origin country, exporter/manufacturer role, and certificate-of-origin route.
- Local or cross-border seller route eligibility.
- Business registration and tax/payee requirements.
- Importer of record or local responsible entity need.
- Product category restricted/prohibited status.
- Product-specific regulator and official source.
- Brand/trademark territory and authorization.
- Label language, warnings, and claims.
- Safety/compliance certificates and test reports.
- Logistics, warehouse, dangerous goods, and customs constraints.
- Renewal/expiry monitoring.
- Manual escalation triggers.

## Country Pack Maturity

| Maturity | Meaning | Use in decision |
|---|---|---|
| `seed` | Initial checklist and source search paths only | Cannot support final decision without fresh source verification |
| `validated` | Requirements verified against official sources recently | Can support decisions with checked dates |
| `production` | Reviewed, versioned, tested with cases, source refresh process exists | Preferred basis for decisions |
| `stale` | Previously useful but source dates exceed freshness policy | Use only after re-verification |

## Current Seed Coverage

The repository includes seed-level packs for:

- `country-US`
- `region-EU`
- `country-UK`
- `country-JP`
- `country-CN-import`
- `region-ASEAN`

These packs improve routing and checklist generation, but they are not authoritative rulebooks. They cannot support final decisions until official sources are attached, freshness is current, and maturity is raised through the governance process.

## Source Discovery By Country

For unknown countries, search official sources in this order:

1. Marketplace official policy for site/category.
2. National product regulator.
3. Customs/import authority.
4. Company/tax registry.
5. Trademark/IP office.
6. Accreditation body or lab/certifier lookup.
7. Standards body.
8. Embassy/trade office or recognized trade association as secondary interpretation.

## Minimum Country Pack Content

A useful country pack should include:

- country code and official country name
- supported marketplace sites or region relationship
- regulator map by product family
- company/KYB source hints
- trademark source hints
- customs/import source hints
- label language rules to verify
- category risk notes
- required evidence types by product family
- source URLs with checked dates
- freshness policy
- known unresolved gaps

## Escalation For Under-Documented Countries

Escalate to human review when:

- official sources cannot be found or are not available in a language the reviewer can verify
- regulated product category has high safety/legal risk
- platform route is unclear
- local representative/importer obligation is unclear
- customs/import route differs by province/free zone/bonded model
- product may be prohibited, controlled, medical, pesticide, child-safety, wireless, food, or supplement-related

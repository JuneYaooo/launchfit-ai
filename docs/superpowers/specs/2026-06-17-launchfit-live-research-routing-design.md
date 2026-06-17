# LaunchFit Live Research Routing Design

## Objective

Make LaunchFit treat information-channel discovery and verification planning as core behavior. Users must provide the product origin and one or more destination markets. The system must produce a per-destination review structure that tells reviewers which authoritative channels to check, what facts to extract, and how unresolved checks affect the decision.

## Scope

The implementation keeps the repository dependency-free. It does not promise live scraping inside the local CLI. Instead, it creates a structured research layer that can be filled by web search, browser automation, platform APIs, registry APIs, or human review later.

## Data Model

Case input adds:

- `origin_country`: required country/region where the product is made, assembled, or shipped from.
- `destination_markets`: required non-empty array of target countries/regions.

Reports add:

- `market_reviews`: one review object per destination market.
- `source_candidates`: recommended source channels per destination.
- `research_tasks`: concrete checks to perform against those channels.

Each market review keeps the destination-specific matched rule packs, source candidates, research tasks, requirements, findings, missing materials, and decision.

## Behavior

Single-market legacy input using `destination_market` is still readable, but new templates emit both `destination_market` and `destination_markets`. Validation requires `origin_country` and at least one destination market.

Multi-market input is split before rulepack matching. `US` and `EU` must become two market reviews, not one merged rule set. The top-level report remains a summary for the whole launch package.

Source candidates cover platform policy, regulator, customs/import, company/KYB, trademark/IP, certification or lab accreditation, standards, logistics/warehouse, and origin/export controls. Research tasks explain what to verify, why it matters, priority, freshness window, source tier, and evidence fields to capture.

## Testing

Use Python `unittest` against pure functions and CLI-compatible payloads. Required coverage:

- bundle validation fails without `origin_country`
- bundle validation fails without `destination_markets`
- bundle validation accepts legacy `destination_market` only when migrated internally by templates is not required; raw new validation remains strict
- launch reports create one `market_reviews` item per destination
- each market review has source candidates and research tasks
- `US, EU` is not treated as one market when `destination_markets` is provided as `["US", "EU"]`


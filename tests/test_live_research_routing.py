import unittest

from launchfit.bundles import bundle_template, validate_case_bundle
from scripts.qualification_audit_schema import launch_report_from_bundle


def minimal_bundle():
    bundle = bundle_template(
        platform="Amazon",
        market="US",
        category="food",
        product="chili sauce",
        origin_country="China",
        destination_markets=["US", "EU"],
    )
    bundle["case"].update(
        {
            "case_id": "multi-market-test",
            "applicant_name": "Example Trading Co., Ltd.",
            "applicant_role": "distributor",
            "business_model": "marketplace_seller",
            "brand_name": "Example Brand",
            "review_date": "2026-06-17",
        }
    )
    bundle["benchmarks"] = [
        {
            "benchmark_id": "BM-001",
            "benchmark_source_type": "direct_competitor",
            "product_name": "Reference Chili Sauce",
            "channel": "Amazon US",
            "channel_role": "search_marketplace",
            "market": "US",
            "positioning": "mainstream",
            "data_basis": "user_provided",
        }
    ]
    bundle["logistics"] = [
        {
            "route_id": "LOG-001",
            "route": "air freight to prep center",
            "mode": "air",
            "cost_basis": "user estimate",
            "data_basis": "user_provided",
        }
    ]
    return bundle


class LiveResearchRoutingTests(unittest.TestCase):
    def test_bundle_validation_requires_origin_country(self):
        bundle = minimal_bundle()
        bundle["case"].pop("origin_country")

        errors, _ = validate_case_bundle(bundle)

        self.assertIn("case.origin_country is required", errors)

    def test_bundle_validation_requires_destination_markets(self):
        bundle = minimal_bundle()
        bundle["case"].pop("destination_markets")

        errors, _ = validate_case_bundle(bundle)

        self.assertIn("case.destination_markets must be a non-empty list", errors)

    def test_launch_report_splits_destination_markets_into_market_reviews(self):
        bundle = minimal_bundle()

        report = launch_report_from_bundle(bundle)

        self.assertEqual(["US", "EU"], [item["destination_market"] for item in report["market_reviews"]])
        self.assertEqual("China", report["case"]["origin_country"])
        self.assertEqual(["US", "EU"], report["case"]["destination_markets"])

    def test_each_market_review_contains_source_candidates_and_research_tasks(self):
        bundle = minimal_bundle()

        report = launch_report_from_bundle(bundle)

        for market_review in report["market_reviews"]:
            self.assertGreaterEqual(len(market_review["source_candidates"]), 6)
            self.assertGreaterEqual(len(market_review["research_tasks"]), 6)
            channel_types = {candidate["channel_type"] for candidate in market_review["source_candidates"]}
            self.assertIn("platform_policy", channel_types)
            self.assertIn("customs_import", channel_types)
            task_keys = {task["task_key"] for task in market_review["research_tasks"]}
            self.assertIn("verify-origin-export-route", task_keys)
            self.assertIn("verify-destination-import-route", task_keys)

    def test_destination_markets_are_not_merged_from_comma_string(self):
        bundle = minimal_bundle()
        bundle["case"]["destination_market"] = "US, EU"
        bundle["case"]["destination_markets"] = ["US", "EU"]

        report = launch_report_from_bundle(bundle)

        self.assertEqual(2, len(report["market_reviews"]))
        self.assertNotIn("US, EU", [item["destination_market"] for item in report["market_reviews"]])

    def test_user_search_channels_are_added_to_candidates_and_tasks(self):
        bundle = minimal_bundle()
        bundle["user_search_channels"] = [
            {
                "channel_id": "user-channel-001",
                "channel_type": "marketplace_search",
                "title": "User Amazon saved search",
                "url": "https://www.amazon.com/s?k=chili+crisp",
                "access_method": "user-provided search URL",
                "applies_to_markets": ["US"],
                "expected_facts": ["current price", "review count", "listing claims"],
                "freshness_days": 7,
            }
        ]

        report = launch_report_from_bundle(bundle)
        us_review = next(item for item in report["market_reviews"] if item["destination_market"] == "US")
        eu_review = next(item for item in report["market_reviews"] if item["destination_market"] == "EU")

        us_candidate_ids = {item["source_candidate_id"] for item in us_review["source_candidates"]}
        eu_candidate_ids = {item["source_candidate_id"] for item in eu_review["source_candidates"]}
        self.assertIn("user-channel-001", us_candidate_ids)
        self.assertNotIn("user-channel-001", eu_candidate_ids)
        self.assertTrue(
            any(task["task_key"] == "verify-user-search-channel" for task in us_review["research_tasks"])
        )


if __name__ == "__main__":
    unittest.main()

import contextlib
import io
import json
import unittest

from launchfit.bundles import bundle_template, validate_case_bundle
from scripts.qualification_audit_schema import (
    launch_report_from_bundle,
    render_detailed_pdf_html,
    render_overview_card_html,
)


class GoToMarketModelTests(unittest.TestCase):
    def test_bundle_template_includes_go_to_market_model(self):
        bundle = bundle_template(
            platform="Amazon",
            market="US",
            category="food",
            product="chili sauce",
            origin_country="China",
            destination_markets=["US"],
            go_to_market_model="cross_border_ecommerce",
        )

        self.assertEqual("cross_border_ecommerce", bundle["case"]["go_to_market_model"])

    def test_physical_trade_bundle_does_not_require_platform(self):
        bundle = bundle_template(
            platform="",
            market="US",
            category="food",
            product="chili sauce",
            origin_country="China",
            destination_markets=["US"],
            go_to_market_model="physical_trade",
        )

        errors, _ = validate_case_bundle(bundle)

        self.assertNotIn("case.platform is required", errors)

    def test_invalid_go_to_market_model_is_rejected(self):
        bundle = bundle_template(
            platform="Amazon",
            market="US",
            category="food",
            product="chili sauce",
            origin_country="China",
            destination_markets=["US"],
            go_to_market_model="cross_border_ecommerce",
        )
        bundle["case"]["go_to_market_model"] = "retail_only"

        errors, _ = validate_case_bundle(bundle)

        self.assertIn("case.go_to_market_model is invalid", errors)

    def test_launch_report_keeps_route_and_prioritizes_physical_trade_checks(self):
        bundle = bundle_template(
            platform="",
            market="US",
            category="food",
            product="chili sauce",
            origin_country="China",
            destination_markets=["US"],
            go_to_market_model="physical_trade",
        )
        bundle["logistics"] = [
            {
                "route": "sea freight to importer warehouse",
                "mode": "sea",
                "cost_basis": "user estimate",
            }
        ]

        report = launch_report_from_bundle(bundle)

        self.assertEqual("physical_trade", report["case"]["go_to_market_model"])
        self.assertEqual("physical_trade", report["go_to_market_route"]["model"])
        self.assertIn("destination import and customs", report["go_to_market_route"]["primary_checks"])
        self.assertNotIn("marketplace listing and category gating", report["go_to_market_route"]["primary_checks"])

    def test_physical_trade_research_tasks_do_not_default_to_platform_policy(self):
        bundle = bundle_template(
            platform="",
            market="US",
            category="food",
            product="chili sauce",
            origin_country="China",
            destination_markets=["US"],
            go_to_market_model="physical_trade",
        )

        report = launch_report_from_bundle(bundle)
        review = report["market_reviews"][0]
        channel_types = {item["channel_type"] for item in review["source_candidates"]}
        task_keys = {item["task_key"] for item in review["research_tasks"]}

        self.assertNotIn("platform_policy", channel_types)
        self.assertNotIn("verify-platform-category-policy", task_keys)
        self.assertIn("offline_channel", channel_types)
        self.assertIn("verify-offline-channel-route", task_keys)

    def test_deliverables_show_go_to_market_path(self):
        bundle = bundle_template(
            platform="Amazon",
            market="US",
            category="food",
            product="chili sauce",
            origin_country="China",
            destination_markets=["US"],
            go_to_market_model="cross_border_ecommerce",
        )
        report = launch_report_from_bundle(bundle)

        card_html = render_overview_card_html(report)
        detail_html = render_detailed_pdf_html(report)

        self.assertIn("Go-to-market path", card_html)
        self.assertIn("cross border ecommerce", card_html)
        self.assertIn("Go-to-market path", detail_html)
        self.assertIn("marketplace listing and category gating", detail_html)

    def test_cli_bundle_template_allows_physical_trade_without_platform(self):
        from scripts.qualification_audit_schema import main

        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            result = main(
                [
                    "bundle-template",
                    "--market",
                    "US",
                    "--category",
                    "food",
                    "--product",
                    "chili sauce",
                    "--origin-country",
                    "China",
                    "--go-to-market-model",
                    "physical_trade",
                    "--destination-market",
                    "US",
                ]
            )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(0, result)
        self.assertEqual("", payload["case"]["platform"])
        self.assertEqual("physical_trade", payload["case"]["go_to_market_model"])


if __name__ == "__main__":
    unittest.main()

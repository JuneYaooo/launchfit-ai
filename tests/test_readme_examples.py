from pathlib import Path
import unittest


class ReadmeExampleTests(unittest.TestCase):
    def test_chinese_readme_does_not_expose_local_server_paths(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertNotIn("/Users/", readme)
        self.assertNotIn("food_hack/test_data", readme)

    def test_chinese_readme_shows_only_one_real_run_card(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("core-card.png", readme)
        self.assertNotIn("detailed-report-long.png", readme)
        self.assertNotIn("front-label.png", readme)
        self.assertNotIn("side-label-origin.png", readme)
        self.assertNotIn("back-label-nutrition.png", readme)

    def test_skill_requires_agent_found_benchmarking(self):
        skill = Path("SKILL.md").read_text(encoding="utf-8")

        self.assertIn("agent 主动检索", skill)
        self.assertIn("用户提供的搜索渠道只能作为补充", skill)
        self.assertIn("不能把找对标的责任推给用户", skill)

    def test_skill_requires_benchmark_images_and_appendix_sources(self):
        skill = Path("SKILL.md").read_text(encoding="utf-8")

        self.assertIn("image_url", skill)
        self.assertIn("对标商品图", skill)
        self.assertIn("appendix", skill)

    def test_benchmark_template_includes_visual_evidence_fields(self):
        from launchfit.benchmarking import benchmark_template

        worksheet = benchmark_template(market="China", category="food", product="olive oil")
        first_row = worksheet["benchmarks"][0]

        self.assertIn("image_url", first_row)
        self.assertIn("image_alt", first_row)


if __name__ == "__main__":
    unittest.main()

from pathlib import Path
import unittest


class ReadmeExampleTests(unittest.TestCase):
    def test_chinese_readme_does_not_expose_local_server_paths(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertNotIn("/Users/", readme)
        self.assertNotIn("food_hack/test_data", readme)

    def test_chinese_readme_shows_real_run_inputs_and_only_one_card(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertIn("core-card.png", readme)
        self.assertIn("front-label.png", readme)
        self.assertIn("side-label-origin.png", readme)
        self.assertIn("back-label-nutrition.png", readme)
        self.assertNotIn("detailed-report-long.png", readme)

    def test_chinese_readme_places_deliverable_links_after_card(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        card_index = readme.index("![Mantova 橄榄油进口中国核心速览卡片]")
        outputs_index = readme.index("- 产物：[详细 PDF]")
        self.assertLess(card_index, outputs_index)
        self.assertIn("[详细 PDF](./examples/real-runs/mantova-olive-oil-china-import/outputs/detailed-report.pdf)", readme)
        self.assertNotIn("input-bundle.json", readme)
        self.assertNotIn("outputs/report.json", readme)
        self.assertNotIn("detailed-report.html", readme)
        self.assertNotIn("core-card.html", readme)

    def test_chinese_readme_prioritizes_audience_and_removes_internal_state_explainer(self):
        readme = Path("README.md").read_text(encoding="utf-8")

        self.assertLess(readme.index("## 适合谁"), readme.index("## 你需要提供什么"))
        self.assertNotIn("下面的示例不是手工 mock", readme)
        self.assertNotIn("## 它怎么判断", readme)
        self.assertNotIn("结构化结论状态", readme)

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

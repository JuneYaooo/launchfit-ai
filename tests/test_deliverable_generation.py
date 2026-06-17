import json
import tempfile
import unittest
from pathlib import Path

from scripts.qualification_audit_schema import (
    launch_report_from_bundle,
    render_detailed_pdf_html,
    render_overview_card_html,
)


FIXTURE = Path("examples/offline-launch-case.json")
REAL_RUN_FIXTURE = Path("examples/real-runs/mantova-olive-oil-china-import/input-bundle.json")


class DeliverableGenerationTests(unittest.TestCase):
    def report(self):
        return launch_report_from_bundle(json.loads(FIXTURE.read_text(encoding="utf-8")))

    def test_overview_card_html_contains_core_decision_sections(self):
        html = render_overview_card_html(self.report())

        self.assertIn("Core Overview Card", html)
        self.assertIn("Origin", html)
        self.assertIn("Destinations", html)
        self.assertIn("Top blockers", html)
        self.assertIn("Must-check channels", html)
        self.assertIn("Next actions", html)

    def test_detailed_pdf_html_contains_auditable_sections(self):
        html = render_detailed_pdf_html(self.report())

        self.assertIn("Detailed LaunchFit Review", html)
        self.assertIn("Per-destination market reviews", html)
        self.assertIn("Source candidates", html)
        self.assertIn("Research tasks", html)
        self.assertIn("Evidence and source status", html)
        self.assertIn("Audit log", html)

    def test_cli_writes_overview_and_detailed_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            review_path = Path(tmp) / "report.json"
            card_path = Path(tmp) / "card.html"
            detail_path = Path(tmp) / "detail.html"
            review_path.write_text(json.dumps(self.report()), encoding="utf-8")

            from scripts.qualification_audit_schema import main

            self.assertEqual(0, main(["launch-report-card", str(review_path), str(card_path)]))
            self.assertEqual(0, main(["launch-report-detail", str(review_path), str(detail_path)]))

            self.assertIn("Core Overview Card", card_path.read_text(encoding="utf-8"))
            self.assertIn("Detailed LaunchFit Review", detail_path.read_text(encoding="utf-8"))

    def test_overview_card_uses_compact_chinese_sections(self):
        html = render_overview_card_html(self.report())

        self.assertIn("出海体检核心卡", html)
        self.assertIn("关键阻断", html)
        self.assertIn("必须核验", html)
        self.assertIn("下一步", html)
        self.assertIn("证据状态", html)
        self.assertIn("section blocker", html)
        self.assertIn("section verify", html)
        self.assertIn("section action", html)

    def test_detailed_pdf_html_is_structured_brief_not_long_letter(self):
        html = render_detailed_pdf_html(self.report())

        self.assertIn("LaunchFit 结构化审核简报", html)
        self.assertIn("一页摘要", html)
        self.assertIn("关键阻断", html)
        self.assertIn("补件清单", html)
        self.assertIn("证据等级", html)
        self.assertNotIn("<h2>Remediation wording</h2>", html)

    def test_detailed_pdf_html_contains_three_engine_full_report(self):
        html = render_detailed_pdf_html(self.report())

        self.assertIn("Engine 1：准入与合规审核", html)
        self.assertIn("Engine 2：本地化适配", html)
        self.assertIn("Engine 3：全链路落地", html)
        self.assertIn("市场准入概览", html)
        self.assertIn("包装本地化", html)
        self.assertIn("渠道与落地路径", html)
        self.assertIn("成本与时间线", html)
        self.assertIn("待查证项", html)
        self.assertIn("三引擎综合建议", html)

    def test_detailed_pdf_html_contains_full_benchmark_analysis_when_rows_exist(self):
        html = render_detailed_pdf_html(self.report())

        self.assertIn("对标分析矩阵", html)
        self.assertIn("价格/规格/单位价", html)
        self.assertIn("包装/标签信号", html)
        self.assertIn("信任/认证信号", html)
        self.assertIn("评论/口碑信号", html)
        self.assertIn("Copy / Avoid / Improve", html)
        self.assertIn("Fly By Jing Sichuan Chili Crisp", html)
        self.assertIn("USD 2.17/oz", html)
        self.assertIn("English front label", html)
        self.assertIn("flavor praise", html)

    def test_real_run_without_benchmarks_outputs_benchmark_research_plan(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_detailed_pdf_html(report)

        self.assertIn("对标调研设计", html)
        self.assertIn("当前不生成虚构竞品结论", html)
        self.assertIn("直接竞品", html)
        self.assertIn("进口替代品", html)
        self.assertIn("平台搜索", html)
        self.assertIn("线下零售", html)
        self.assertIn("价格/规格/单位价", html)
        self.assertIn("包装/标签信号", html)
        self.assertIn("评论/口碑信号", html)

    def test_real_run_card_is_compact_for_readme_preview(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_overview_card_html(report)

        self.assertNotIn("min-height: 1600px", html)
        self.assertNotIn("min-height: 1496px", html)
        self.assertNotIn("Chinese label artwork", html)
        self.assertNotIn("Unsupported claims", html)
        self.assertIn("width: 1200px", html)

    def test_real_run_detailed_report_hides_raw_machine_fallbacks(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_detailed_pdf_html(report)

        self.assertNotIn("Requirement is not yet matched to submitted applicant/product evidence.", html)
        self.assertNotIn("Holder &#x27;", html)
        self.assertNotIn("Confirm the document covers", html)
        self.assertNotIn("Competitor rows are offline", html)
        self.assertNotIn("Marketplace restricted product policy", html)
        self.assertNotIn("No packaging benchmark signals supplied", html)
        self.assertNotIn("destination import and customs", html)
        self.assertIn("文件持有人与待确认进口商/经销商不一致", html)

    def test_real_run_detailed_report_keeps_full_olive_oil_review_context(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_detailed_pdf_html(report)

        self.assertIn("Mantova Equilibrato 特级初榨橄榄油 250ml", html)
        self.assertIn("中国食品进口路径", html)
        self.assertIn("中文标签", html)
        self.assertIn("原产地证", html)
        self.assertIn("进口商/清关", html)
        self.assertIn("供应链与物流", html)
        self.assertIn("服务商与责任方", html)
        self.assertIn("来源候选", html)
        self.assertIn("核验任务", html)
        self.assertIn("T1/T2 权威入口", html)


if __name__ == "__main__":
    unittest.main()

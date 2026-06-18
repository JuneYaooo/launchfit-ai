import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.qualification_audit_schema import (
    _write_html_or_export,
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

    def test_launch_report_records_generation_metadata(self):
        with patch.dict(
            "os.environ",
            {
                "LAUNCHFIT_AGENT_NAME": "Hermes",
                "LAUNCHFIT_MODEL_NAME": "test-model",
                "LAUNCHFIT_SEARCH_METHODS": "browser search, customs registry",
            },
        ):
            report = self.report()

        metadata = report["generation_metadata"]
        self.assertEqual("Hermes", metadata["agent"])
        self.assertEqual("test-model", metadata["model"])
        self.assertIn("browser search", metadata["search_methods"])
        self.assertIn("customs registry", metadata["search_methods"])
        self.assertIn("generated_at", metadata)

    def test_report_renderers_include_generation_provenance(self):
        report = self.report()

        card_html = render_overview_card_html(report)
        detail_html = render_detailed_pdf_html(report)

        self.assertNotIn("生成说明", card_html)
        self.assertNotIn("Agent", card_html)
        self.assertNotIn("搜索途径", card_html)
        self.assertIn("生成说明", detail_html)
        self.assertIn("Agent", detail_html)
        self.assertIn("Codex", detail_html)
        self.assertIn("模型", detail_html)
        self.assertIn("未声明", detail_html)
        self.assertIn("搜索途径", detail_html)

    def test_pdf_export_suppresses_browser_header_footer_file_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "detail.pdf"
            with patch("scripts.qualification_audit_schema._chrome_path", return_value="/bin/echo"):
                with patch("scripts.qualification_audit_schema.subprocess.run") as run:
                    self.assertEqual(0, _write_html_or_export(str(output_path), "<html></html>", "detail"))

            command = run.call_args.args[0]
            self.assertIn("--no-pdf-header-footer", command)
            self.assertIn("--print-to-pdf-no-header", command)

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

    def test_real_run_contains_agent_found_china_benchmark_rows(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_detailed_pdf_html(report)

        self.assertGreaterEqual(len(report["market_benchmarks"]), 8)
        self.assertNotIn("暂无可分析竞品样本", html)
        self.assertIn("欧丽薇兰 Olivoila 特级初榨橄榄油 250ml", html)
        self.assertIn("伯爵 BORGES 特级初榨橄榄油 250ml", html)
        self.assertIn("晟麦 sanmark 特级初榨橄榄油 250ml", html)
        self.assertIn("约¥0.109-0.128/ml", html)
        self.assertIn("已实时核验", html)
        self.assertIn("京东自营", html)
        self.assertIn("保真橄榄油", html)
        self.assertIn("对标来源与核验边界", html)
        self.assertIn("附件 A：来源链接清单", html)
        main_report, source_appendix = html.split("附件 A：来源链接清单", 1)
        self.assertNotIn("https://search.jd.com", main_report)
        self.assertIn("https://search.jd.com", source_appendix)
        self.assertIn("商业市场信号", html)
        self.assertIn("2026-06-18", html)

    def test_benchmark_source_boundary_is_appendix_only(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_detailed_pdf_html(report)

        main_report, source_appendix = html.split("附件 A：来源链接清单", 1)
        self.assertNotIn("对标来源与核验边界", main_report)
        self.assertIn("对标来源与核验边界", source_appendix)

    def test_detailed_report_renders_benchmark_product_images_when_supplied(self):
        bundle = json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8"))
        bundle["benchmarks"][0]["image_url"] = "https://img.example.test/olivoila-250ml.jpg"
        bundle["benchmarks"][0]["image_alt"] = "Olivoila 250ml bottle front pack"

        report = launch_report_from_bundle(bundle)
        html = render_detailed_pdf_html(report)

        self.assertEqual("https://img.example.test/olivoila-250ml.jpg", report["market_benchmarks"][0]["image_url"])
        self.assertIn("对标商品图", html)
        self.assertIn("https://img.example.test/olivoila-250ml.jpg", html)
        self.assertIn("Olivoila 250ml bottle front pack", html)

    def test_real_run_benchmark_visuals_include_verified_images_and_packaging_observations(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_detailed_pdf_html(report)

        image_rows = [row for row in report["market_benchmarks"] if row.get("image_url")]
        self.assertGreaterEqual(len(image_rows), 5)
        self.assertIn("对标商品图", html)
        self.assertIn("包装观察", html)
        self.assertIn("对标包装观察", html)
        self.assertIn("250ml/小规格是入门试用锚点", html)
        self.assertIn("玻璃瓶/罐装", html)
        self.assertIn("250ml小瓶", html)
        self.assertIn("250ml罐装", html)
        self.assertIn("https://img14.360buyimg.com/n7/jfs/t1/394048/11/16981/116939/699e9de6F218ed786/008332032047c134.jpg", html)
        self.assertIn("https://img14.360buyimg.com/n7/jfs/t1/338298/12/2504/102986/68aeb6f0F170dabc6/29226067d72c5e23.jpg", html)

    def test_real_run_generation_metadata_names_search_routes(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_detailed_pdf_html(report)

        self.assertIn("agent 主动检索", report["generation_metadata"]["search_methods"])
        self.assertIn("公开商业搜索/对标检索", report["generation_metadata"]["search_methods"])
        self.assertIn("agent 主动检索", html)
        self.assertIn("公开商业搜索/对标检索", html)

    def test_real_run_card_is_compact_for_readme_preview(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_overview_card_html(report)

        self.assertNotIn("min-height: 1600px", html)
        self.assertNotIn("min-height: 1496px", html)
        self.assertNotIn("Chinese label artwork", html)
        self.assertNotIn("Unsupported claims", html)
        self.assertIn("width: 1200px", html)

    def test_real_run_card_is_distilled_from_detailed_report_signals(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_overview_card_html(report)

        self.assertIn("详细报告提炼", html)
        self.assertIn("对标信号", html)
        self.assertIn("价格体检", html)
        self.assertIn("渠道体检", html)
        self.assertIn("包装/卖点体检", html)
        self.assertIn("约¥0.109-0.128/ml", html)
        self.assertIn("京东自营", html)
        self.assertNotIn("信任信号", html)
        self.assertNotIn("10000+评价入口", html)
        self.assertIn("正文依据见详细 PDF", html)
        self.assertNotIn("https://search.jd.com", html)
        self.assertNotIn("对标来源与核验边界", html)

    def test_real_run_card_uses_decision_dashboard_layout(self):
        report = launch_report_from_bundle(json.loads(REAL_RUN_FIXTURE.read_text(encoding="utf-8")))
        html = render_overview_card_html(report)

        self.assertIn("当前动作", html)
        self.assertIn("暂缓推进", html)
        self.assertIn("判断链路", html)
        self.assertIn("1. 准入风险", html)
        self.assertIn("2. 本地化缺口", html)
        self.assertIn("3. 市场对标", html)
        self.assertIn("4. 落地条件", html)
        self.assertIn("进口主体", html)
        self.assertIn("清关文件", html)
        self.assertIn("标签审核", html)
        self.assertIn("物流预算", html)
        self.assertNotIn(">目标国监管</span>", html)
        self.assertNotIn(">海关进口</span>", html)
        self.assertIn("优先级", html)
        self.assertIn("风险债务", html)
        self.assertIn("不是产品问题", html)

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

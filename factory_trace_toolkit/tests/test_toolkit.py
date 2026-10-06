"""English: Regress ingest lineage, queries, scoring, bounded fetch, and model logs.

中文：以合成文件与本地 HTTP 服务回归采集谱系、检索、评分、下载与模型日志；不访问生产客户数据或平台账号。
"""
from __future__ import annotations

import csv
import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from PIL import Image, ImageDraw


TOOLKIT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLKIT_ROOT / "src"))

from factorytrace.audit import audit_case  # noqa: E402
from factorytrace.cli import main as cli_main  # noqa: E402
from factorytrace.compare import automatic_worker_count, compare_images  # noqa: E402
from factorytrace.environment import build_environment_report  # noqa: E402
from factorytrace.fetch import fetch_queue  # noqa: E402
from factorytrace.init_case import create_case  # noqa: E402
from factorytrace.intake import ingest  # noqa: E402
from factorytrace.ledger import build_ledger_rows, sync_ledger  # noqa: E402
from factorytrace.materials import check_materials  # noqa: E402
from factorytrace.provenance import log_model_use  # noqa: E402
from factorytrace.queries import build_queries  # noqa: E402
from factorytrace.scoring import DIMENSIONS, score_candidate  # noqa: E402
from factorytrace.variants import generate_variants  # noqa: E402


class QuietHandler(BaseHTTPRequestHandler):
    payload = b"<html><title>Factory evidence fixture</title><body>ok</body></html>"

    def do_GET(self) -> None:  # noqa: N802
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, format: str, *args: object) -> None:
        return


class ToolkitTests(unittest.TestCase):
    def make_image(self, path: Path) -> None:
        image = Image.new("RGB", (160, 100), "white")
        draw = ImageDraw.Draw(image)
        draw.rounded_rectangle((10, 10, 150, 90), radius=12, fill="#999999")
        draw.ellipse((112, 58, 136, 82), fill="black")
        draw.text((20, 20), "LOGO", fill="red")
        image.save(path, format="PNG")

    def test_init_and_duplicate_content_different_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("中文 案例", root)
            source = root / "来源"
            source.mkdir()
            (source / "照片一.bin").write_bytes(b"same-content")
            (source / "photo-two.bin").write_bytes(b"same-content")
            records = ingest(
                [source],
                case,
                relationship="test",
                recursive=True,
                workers=4,
            )
            self.assertEqual(len(records), 2)
            manifest = json.loads((case / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["artifacts"]), 2)
            self.assertEqual(
                len({item["relative_path"] for item in manifest["artifacts"]}), 2
            )
            ingest(
                [source],
                case,
                relationship="test",
                recursive=True,
                workers=4,
            )
            manifest = json.loads((case / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["artifacts"]), 2)

    def test_resume_migrates_search_log_without_losing_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("resume", root)
            search_log = case / "output" / "search_log.csv"
            search_log.write_text(
                "run_id,query_id,engine,notes\n"
                "RUN-1,Q-1,Lens,keep-me\n",
                encoding="utf-8",
            )
            create_case("resume", root, resume=True)
            with search_log.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                rows = list(reader)
                fields = set(reader.fieldnames or [])
            self.assertIn("failure_reason", fields)
            self.assertEqual(rows[0]["notes"], "keep-me")
            self.assertTrue(
                search_log.with_suffix(".csv.pre-1.1.bak").is_file()
            )

    def test_variants_have_lineage_crop_and_brand_mask(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("variants", root)
            image_path = root / "source.png"
            self.make_image(image_path)
            manifest_path = generate_variants(
                image_path,
                case,
                crops=["hole=100,45,50,45"],
                masks=["brand=15,15,60,25"],
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(len(manifest["variants"]), 4)
            self.assertIn("no generative edit", manifest["policy"])
            self.assertTrue(all(item["sha256"] for item in manifest["variants"]))

    def test_query_generator_does_not_use_irrelevant_brand_positively(self) -> None:
        profile = {
            "category_zh": "虚构演示阀壳",
            "category_en": "synthetic valve housing",
            "brand_policy": "ignore",
            "visible_brands": ["IRRELEVANT_LOGO"],
            "dimensions_mm": {"outer_length": 100, "outer_width": 60},
            "features_zh": ["演示侧孔", "演示安装凸缘"],
            "features_en": ["synthetic side port", "synthetic mounting flange"],
            "processes_zh": ["机加工"],
            "processes_en": ["machining"],
            "parts_zh": ["演示壳体"],
            "parts_en": ["synthetic housing"],
        }
        rows = build_queries(profile)
        with_brand = [row["query"] for row in rows if "IRRELEVANT_LOGO" in row["query"]]
        self.assertTrue(with_brand)
        self.assertTrue(
            all('-"IRRELEVANT_LOGO"' in query for query in with_brand)
        )

    def test_scoring_requires_structured_independent_evidence(self) -> None:
        evidence = []
        source_pairs = [
            ("government", "GOV"),
            ("buyer_document", "BUYER"),
        ]
        for dimension in DIMENSIONS:
            for source_class, group in source_pairs:
                evidence.append(
                    {
                        "evidence_id": f"{dimension}-{group}",
                        "dimension": dimension,
                        "stance": "support",
                        "strength": "direct",
                        "source_class": source_class,
                        "independence_group": f"{group}-{dimension}",
                        "entity_bind": "exact",
                        "site_bind": "exact",
                        "sku_bind": "exact",
                        "process": "deep_draw",
                        "local_path": "evidence/factory/fixture.bin",
                    }
                )
        candidate = {
            "candidate_id": "CAND-PASS",
            "display_name": "Fixture",
            "target_processes": ["deep_draw"],
            "entities": {
                "contracting_entity": "A",
                "payment_entity": "A",
                "manufacturer_entity": "B",
                "manufacturing_sites": ["Site 1"],
                "exact_sku": "SKU-1",
            },
            "responsibility_chain_explanation": "A contracts and B manufactures under agreement.",
            "evidence": evidence,
            "red_flags": [],
        }
        result = score_candidate(candidate)
        self.assertTrue(result["verdict"].startswith("A /"))
        self.assertEqual(
            result["hard_gates_passed"], result["hard_gates_total"]
        )
        self.assertLessEqual(result["confidence_index"], 95)

        unproven = score_candidate(
            {
                "candidate_id": "CAND-FAIL",
                "target_processes": ["deep_draw"],
                "entities": {},
                "responsibility_chain_explanation": "",
                "evidence": [],
                "red_flags": [],
            }
        )
        self.assertTrue(unproven["verdict"].startswith("D /"))

    def test_audit_rejects_forged_manual_verdict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("audit", root)
            candidate_path = case / "candidates" / "CAND-001.json"
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["declared_verdict"] = "A / confirmed target-process manufacturer"
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            report = audit_case(case, "research")
            self.assertEqual(report["status"], "FAIL")
            self.assertTrue(
                any("declared verdict conflicts" in item for item in report["errors"])
            )

    def test_parallel_fetch_captures_body_and_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("fetch", root)
            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                queue = case / "evidence" / "url_queue.csv"
                with queue.open("w", encoding="utf-8-sig", newline="") as stream:
                    writer = csv.DictWriter(
                        stream,
                        fieldnames=["id", "url", "candidate_id", "kind", "notes"],
                    )
                    writer.writeheader()
                    writer.writerow(
                        {
                            "id": "LOCAL-1",
                            "url": f"http://127.0.0.1:{server.server_port}/evidence",
                            "candidate_id": "CAND-LOCAL",
                            "kind": "html",
                            "notes": "local fixture",
                        }
                    )
                results = fetch_queue(
                    queue,
                    case,
                    workers=4,
                    per_host=2,
                    delay=0,
                    retries=1,
                    respect_robots=False,
                )
                self.assertEqual(results[0]["status"], "downloaded")
                self.assertEqual(results[0]["content_length"], len(QuietHandler.payload))
                self.assertTrue(results[0]["sha256"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)

    def test_environment_report_requires_no_model(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = build_environment_report(
                anchor=Path(temporary),
                requested_profile="minimum",
                model_mode="none",
            )
            self.assertTrue(report["model"]["required_by_core"] is False)
            self.assertEqual(report["model"]["declared_mode"], "none")
            self.assertIn("Pillow", report["dependencies"])
            proxy_keys = list(
                report["network_runtime"]["proxy_variables_present"]
            )
            self.assertEqual(
                len(proxy_keys),
                len({key.casefold() for key in proxy_keys}),
            )
            self.assertIn(report["status"], {"PASS", "FAIL"})

    def test_compare_auto_workers_are_capped_and_operational(self) -> None:
        self.assertLessEqual(automatic_worker_count(1000), 8)
        self.assertEqual(automatic_worker_count(1), 1)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            reference = root / "reference.png"
            candidate = root / "candidate.png"
            self.make_image(reference)
            self.make_image(candidate)
            output = root / "comparison.csv"
            rows = compare_images(reference, [candidate], output, workers=0)
            self.assertEqual(len(rows), 1)
            self.assertTrue(output.is_file())
            self.assertEqual(rows[0]["triage_similarity"], "100.00")
            with self.assertRaises(ValueError):
                compare_images(reference, [candidate], output, workers=-1)
            with self.assertRaises(ValueError):
                compare_images(reference, [candidate], output, workers=62)

    def test_material_gate_checks_files_and_manual_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("materials", root)
            image = case / "artifacts" / "original" / "overview.png"
            self.make_image(image)
            plan_path = case / "work" / "materials_plan.json"
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
            for item in plan["items"]:
                if item["required_from"] == "discovery":
                    item["status"] = "verified"
                    if item["item_id"] == "P0-01":
                        item["paths"] = [
                            image.relative_to(case).as_posix()
                        ]
                        item["min_long_edge_px"] = 100
            plan_path.write_text(
                json.dumps(plan, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            report = check_materials(case, plan_path, stage="discovery")
            self.assertEqual(report["status"], "PASS")
            report = check_materials(case, plan_path, stage="comparison")
            self.assertEqual(report["status"], "FAIL")

    def test_cli_records_execution_without_query_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exit_code = cli_main(
                [
                    "init",
                    "logged-case",
                    "--root",
                    str(root),
                ]
            )
            self.assertEqual(exit_code, 0)
            case = root / "logged-case"
            source = root / "source.bin"
            source.write_bytes(b"log-redaction")
            exit_code = cli_main(
                [
                    "ingest",
                    str(source),
                    "--case-root",
                    str(case),
                    "--source-url",
                    "https://example.invalid/item?token=SHOULD_NOT_APPEAR",
                ]
            )
            self.assertEqual(exit_code, 0)
            with (case / "logs" / "execution_log.csv").open(
                encoding="utf-8-sig", newline=""
            ) as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 2)
            self.assertTrue(all(row["status"] == "success" for row in rows))
            rendered = json.dumps(rows, ensure_ascii=False)
            self.assertIn("factorytrace", rendered)
            self.assertNotIn("SHOULD_NOT_APPEAR", rendered)
            self.assertIn("[REDACTED_QUERY]", rendered)
            manifest = json.loads(
                (case / "manifest.json").read_text(encoding="utf-8")
            )
            manifest_rendered = json.dumps(manifest, ensure_ascii=False)
            self.assertNotIn("SHOULD_NOT_APPEAR", manifest_rendered)
            self.assertIn("REDACTED", manifest_rendered)

    def test_ledger_is_generated_from_candidate_canonical_data(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("ledger", root)
            candidate_path = case / "candidates" / "CAND-001.json"
            candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
            candidate["evidence"] = [
                {
                    "evidence_id": "EV-001",
                    "claim_id": "",
                    "role": "component_maker",
                    "component": "tray_body",
                    "dimension": "physical_site_process",
                    "stance": "support",
                    "strength": "lead",
                    "source_class": "self_published",
                    "independence_group": "SUPPLIER-1",
                    "entity_bind": "partial",
                    "site_bind": "none",
                    "sku_bind": "family",
                    "process": "deep_draw",
                    "source_url": "https://example.invalid/product",
                    "observed_fact": "Candidate shows a tray.",
                    "limitations": "Self-published and not site-bound.",
                }
            ]
            candidate_path.write_text(
                json.dumps(candidate, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            rows = build_ledger_rows(case)
            self.assertEqual(rows[0]["evidence_id"], "EV-001")
            output = sync_ledger(case)
            with output.open(encoding="utf-8-sig", newline="") as stream:
                ledger_rows = list(csv.DictReader(stream))
            self.assertEqual(ledger_rows[0]["component"], "tray_body")

    def test_model_log_is_non_evidentiary_and_hashes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            case = create_case("model-log", root)
            output = case / "work" / "model-output.json"
            output.write_text('{"hypothesis": true}\n', encoding="utf-8")
            row = log_model_use(
                case,
                mode="cloud",
                provider_or_runtime="fixture",
                model_id="fixture-model",
                model_revision="test",
                quantization="",
                endpoint_class="chat",
                prompt_id="PROMPT-TEST",
                input_artifact_ids=["ART-001"],
                output_path=output,
                human_verified=False,
                notes="unit test",
            )
            self.assertEqual(row["evidence_eligible"], "false")
            self.assertIn("output_sha256=", row["notes"])
            with (case / "logs" / "model_usage_log.csv").open(
                encoding="utf-8-sig", newline=""
            ) as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]["model_id"], "fixture-model")


if __name__ == "__main__":
    unittest.main()

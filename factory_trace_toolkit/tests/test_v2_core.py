"""English: Regress multi-axis attribution, source independence, and non-destructive migration.

中文：回归多轴归因、来源独立性与非破坏迁移；能力、地区偏好或零件认证不能替代完整批次生产链。
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLKIT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLKIT_ROOT / "src"))

from factorytrace.assessment import HYPOTHESES, assess_candidate  # noqa: E402
from factorytrace.migration import (  # noqa: E402
    MigrationError,
    migrate_candidate_v1_to_v2,
    migrate_json_file,
)
from factorytrace.schema_validation import (  # noqa: E402
    SchemaDependencyError,
    validate_instance,
)
from factorytrace.scoring import score_candidate  # noqa: E402


class V2CoreTests(unittest.TestCase):
    def candidate(self) -> dict:
        return {
            "schema": 1,
            "candidate_id": "CAND-V2",
            "display_name": "Fixture factory",
            "target_processes": ["stamping"],
            "entities": {
                "contracting_entity": "Buyer",
                "payment_entity": "Buyer",
                "manufacturer_entity": "Factory",
                "manufacturing_sites": ["Site A"],
                "exact_sku": "SKU-A",
            },
            "responsibility_chain_explanation": "Buyer contracts Factory.",
            "evidence": [],
            "red_flags": [],
        }

    def evidence(
        self,
        evidence_id: str,
        dimension: str,
        *,
        source_url: str,
        process: str = "stamping",
        site_bind: str = "exact",
        sku_bind: str = "exact",
        source_class: str = "government",
        batch_id: str = "",
    ) -> dict:
        return {
            "evidence_id": evidence_id,
            "dimension": dimension,
            "stance": "support",
            "strength": "direct",
            "source_class": source_class,
            "independence_group": f"declared-{evidence_id}",
            "entity_bind": "exact",
            "site_bind": site_bind,
            "sku_bind": sku_bind,
            "process": process,
            "source_url": source_url,
            "captured_at_utc": "2026-08-01T00:00:00Z",
            "observed_fact": "fixture fact",
            "limitations": "fixture limitation",
            "review_status": "accepted",
            "batch_id": batch_id,
        }

    def test_multiaxis_output_and_deprecated_alias(self) -> None:
        result = score_candidate(self.candidate())
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(result["trace_stage"], "S0_UNLINKED")
        self.assertIn(result["analytic_confidence"], {"LOW", "MODERATE", "HIGH"})
        self.assertEqual(
            result["confidence_index"], result["evidence_sufficiency_score"]
        )
        self.assertTrue(result["confidence_index_deprecated"])
        self.assertIn("not a statistically calibrated probability", result["confidence_notice"])
        self.assertEqual(
            {item["id"] for item in result["ach"]["hypotheses"]},
            set(HYPOTHESES),
        )

    def test_same_source_url_is_one_independence_cluster(self) -> None:
        candidate = self.candidate()
        candidate["evidence"] = [
            self.evidence(
                f"EV-{index}",
                "physical_site_process",
                source_url=f"https://example.test/report?utm_source={index}",
                sku_bind="none",
            )
            for index in range(20)
        ]
        result = assess_candidate(candidate)
        groups = result["components"]["physical_site_process"]["support_groups"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(result["ach"]["independent_source_clusters"], 1)

    def test_capable_factory_stays_unlinked(self) -> None:
        candidate = self.candidate()
        candidate["evidence"] = [
            self.evidence(
                "EV-CAPABILITY",
                "physical_site_process",
                source_url="https://gov.example/factory-equipment",
                sku_bind="none",
            )
        ]
        result = assess_candidate(candidate)
        self.assertEqual(result["trace_stage"], "S0_UNLINKED")
        self.assertGreater(result["capability_fit_score"], 70)
        h2 = next(item for item in result["ach"]["hypotheses"] if item["id"] == "H2")
        self.assertGreater(h2["net_consistency"], 0)

    def test_trace_stage_reaches_batch_only_with_full_chain(self) -> None:
        candidate = self.candidate()
        candidate["evidence"] = [
            self.evidence(
                "EV-SKU",
                "exact_sku_process",
                source_url="https://audit.example/exact-product",
                source_class="independent_audit",
            ),
            self.evidence(
                "EV-CERT-SITE",
                "certification_manufacturing_site",
                source_url="https://cert.example/site",
                source_class="certifier",
            ),
            self.evidence(
                "EV-BATCH",
                "commercial_batch_chain",
                source_url="https://buyer.example/packing-list",
                source_class="buyer_document",
                batch_id="BATCH-001",
            ),
        ]
        result = assess_candidate(candidate)
        self.assertEqual(result["trace_stage"], "S4_BATCH_LINKED")

    def test_mainland_filter_does_not_change_attribution_axes(self) -> None:
        base = self.candidate()
        base["evidence"] = [
            self.evidence(
                "EV-CAPABILITY",
                "physical_site_process",
                source_url="https://gov.example/factory-equipment",
                sku_bind="none",
            )
        ]
        mainland = copy.deepcopy(base)
        mainland["verified_mainland_site"] = True
        overseas = copy.deepcopy(base)
        overseas["verified_mainland_site"] = False
        left = assess_candidate(mainland)
        right = assess_candidate(overseas)
        for key in (
            "trace_stage",
            "analytic_confidence",
            "analytic_confidence_score",
            "evidence_sufficiency_score",
            "capability_fit_score",
            "ach",
        ):
            self.assertEqual(left[key], right[key], key)
        self.assertIsNotNone(left["procurement_utility"])
        self.assertIsNone(right["procurement_utility"])

    def test_component_certification_fails_dual_complete_product_gate(self) -> None:
        candidate = self.candidate()
        candidate["certification"] = {
            "ul": {
                "status": "Active",
                "target_exact_match": True,
                "authorized_site_confirmed": True,
                "complete_product": False,
                "certification_type": "Recognized Component",
            },
            "watermark": {
                "status": "Active",
                "target_exact_match": True,
                "authorized_site_confirmed": True,
                "complete_product": True,
            },
        }
        result = assess_candidate(candidate)
        self.assertEqual(result["certification_state"]["ul"]["state"], "COMPONENT_ONLY")
        self.assertEqual(result["certification_state"]["dual_certification_gate"], "FAIL")

    def test_v1_migration_is_non_destructive_and_quarantines_manual_scores(self) -> None:
        source = self.candidate()
        source["confidence_index"] = 59
        source["research_assessment"] = {"source_probability_percent": 59}
        before = copy.deepcopy(source)
        migrated = migrate_candidate_v1_to_v2(
            source, migrated_at_utc="2026-08-01T00:00:00Z"
        )
        self.assertEqual(source, before)
        self.assertEqual(migrated["schema_version"], 2)
        self.assertNotIn("confidence_index", migrated)
        self.assertEqual(
            migrated["legacy_manual_score"]["values"]["confidence_index"], 59
        )
        self.assertTrue(
            migrated["legacy_manual_score"]["excluded_from_v2_assessment"]
        )
        self.assertEqual(migrated["verified_mainland_site"], "unknown")
        self.assertEqual(len(migrated["hypotheses"]), 5)

    def test_file_migration_refuses_in_place_and_preserves_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "candidate.json"
            source.write_text(json.dumps(self.candidate()), encoding="utf-8")
            before = source.read_bytes()
            with self.assertRaises(MigrationError):
                migrate_json_file(source, source)
            destination = migrate_json_file(source)
            self.assertEqual(source.read_bytes(), before)
            self.assertTrue(destination.is_file())

    def test_v2_candidate_and_assessment_schemas(self) -> None:
        candidate = migrate_candidate_v1_to_v2(
            self.candidate(), migrated_at_utc="2026-08-01T00:00:00Z"
        )
        assessment = assess_candidate(candidate)
        try:
            validate_instance(candidate, "candidate.v2.schema.json")
            validate_instance(assessment, "assessment.v2.schema.json")
        except SchemaDependencyError as error:
            self.assertIn("python -m pip install", str(error))


if __name__ == "__main__":
    unittest.main()

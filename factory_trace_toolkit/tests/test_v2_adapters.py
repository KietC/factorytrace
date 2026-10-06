"""English: Regress certification, social, event, and process-pack hard gates.

中文：回归认证、社媒、事件与工艺包硬门槛；测试覆盖伪造封装、变更摘要与角色混淆，未知不能当作通过。
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


TOOLKIT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLKIT_ROOT / "src"))

from factorytrace.certification import evaluate_certification  # noqa: E402
from factorytrace.events import validate_event_chain  # noqa: E402
from factorytrace.process_packs import (  # noqa: E402
    evaluate_process_pack,
    list_process_packs,
    load_process_pack,
    validate_process_pack,
)
from factorytrace.social import evaluate_social_chain  # noqa: E402


class CertificationAdapterTests(unittest.TestCase):
    def certification(self, scheme: str = "WaterMark") -> dict[str, object]:
        return {
            "scheme": scheme,
            "certificate_id": f"{scheme}-FILE-1",
            "status": "active",
            "valid_from": "2026-01-01",
            "valid_to": "2027-01-01",
            "roles": {
                "licence_holder": [{"party_id": "BRAND-1"}],
                "listee": [{"party_id": "BRAND-1"}],
                "manufacturer": [{"party_id": "MFG-1"}],
            },
            "products": [
                {
                    "model": "SV-316-10",
                    "materials": ["AISI 316"],
                    "ratings": {
                        "set_pressure": {"value": 0.7, "unit": "MPa"},
                        "temperature": {"value": 99, "unit": "degC"},
                    },
                    "certification_type": "finished_product",
                    "authorized_site_ids": ["SITE-JM-1"],
                },
                {
                    "model": "SV-304-10",
                    "materials": ["AISI 304"],
                    "ratings": {
                        "set_pressure": {"value": 0.7, "unit": "MPa"},
                        "temperature": {"value": 99, "unit": "degC"},
                    },
                    "certification_type": "finished_product",
                    "authorized_site_ids": ["SITE-JM-1"],
                },
            ],
            "authorized_sites": [
                {
                    "site_id": "SITE-JM-1",
                    "manufacturer_party_id": "MFG-1",
                    "status": "active",
                    "valid_from": "2026-01-01T00:00:00Z",
                    "valid_to": "2027-01-01T00:00:00Z",
                    "processes": ["assembly", "pressure_test"],
                }
            ],
        }

    def target(self) -> dict[str, object]:
        return {
            "model": "SV-316-10",
            "material": "AISI 316",
            "ratings": {
                "set_pressure": {"value": "0.70", "unit": "mpa"},
                "temperature": {"value": 99, "unit": "degC"},
            },
            "certification_type": "finished_product",
            "site_id": "SITE-JM-1",
            "manufacturer_party_id": "MFG-1",
        }

    def test_exact_scope_and_explicit_manufacturer_site_pass(self) -> None:
        result = evaluate_certification(
            self.certification(), self.target(), at="2026-08-01T00:00:00Z"
        )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["role_bindings"]["licence_holder"][0]["party_id"], "BRAND-1")
        self.assertEqual(result["role_bindings"]["manufacturer"][0]["party_id"], "MFG-1")
        self.assertTrue(result["gates"]["single_scope_conjunction"]["passed"])

    def test_material_type_site_role_and_validity_are_independent_hard_gates(self) -> None:
        mutations = []

        wrong_material_target = self.target()
        wrong_material_target["material"] = "AISI 304"
        mutations.append(
            (self.certification(), wrong_material_target, "exact_material", "2026-08-01T00:00:00Z")
        )

        wrong_type_target = self.target()
        wrong_type_target["certification_type"] = "recognized_component"
        mutations.append(
            (
                self.certification(),
                wrong_type_target,
                "exact_certification_type",
                "2026-08-01T00:00:00Z",
            )
        )

        wrong_site_target = self.target()
        wrong_site_target["site_id"] = "SITE-OTHER"
        mutations.append(
            (self.certification(), wrong_site_target, "authorized_site_exact", "2026-08-01T00:00:00Z")
        )

        no_manufacturer = copy.deepcopy(self.certification())
        no_manufacturer["roles"].pop("manufacturer")
        mutations.append(
            (no_manufacturer, self.target(), "explicit_manufacturer_role", "2026-08-01T00:00:00Z")
        )

        mutations.append(
            (self.certification(), self.target(), "certificate_valid_at", "2028-08-01T00:00:00Z")
        )

        for record, target, failed_gate, at in mutations:
            with self.subTest(failed_gate=failed_gate):
                result = evaluate_certification(record, target, at=at)
                self.assertEqual(result["status"], "FAIL")
                self.assertFalse(result["gates"][failed_gate]["passed"])


class SocialAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.account = {
            "platform": "LinkedIn",
            "account_id": "li-company-1",
            "entity_id": "MFG-1",
            "status": "active",
            "verification": {"verified": True, "type": "page"},
        }
        self.target = {
            "entity_id": "MFG-1",
            "site_id": "SITE-JM-1",
            "process": "pressure_test",
            "sku": "SV-316-10",
        }

    def test_platform_verification_closes_entity_only(self) -> None:
        result = evaluate_social_chain(self.account, [], self.target)
        self.assertEqual(result["binding_state"], "ENTITY_BOUND")
        self.assertNotIn("SITE_BOUND", result["binding_path"])
        self.assertTrue(result["platform_entity_verified"])

    def test_blocked_access_is_not_absence(self) -> None:
        account = dict(self.account)
        account["status"] = "login_required"
        result = evaluate_social_chain(account, [], self.target)
        self.assertEqual(result["access"]["state"], "BLOCKED")
        self.assertFalse(result["access"]["absence_allowed"])
        self.assertEqual(result["absence_conclusion"], "UNKNOWN_BLOCKED_NOT_ABSENCE")

    def test_target_binding_and_same_origin_reposts_are_deduplicated(self) -> None:
        binding = {
            "entity_id": "MFG-1",
            "site_id": "SITE-JM-1",
            "process": "pressure_test",
            "sku": "SV-316-10",
        }
        observations = [
            {
                "evidence_id": "SOC-1",
                "origin_content_id": "VIDEO-ORIGIN-1",
                "relationship": "native_original",
                "media_sha256": "a" * 64,
                "bindings": binding,
            },
            {
                "evidence_id": "SOC-2",
                "origin_content_id": "VIDEO-ORIGIN-1",
                "relationship": "exact_reupload",
                "bindings": binding,
            },
        ]
        result = evaluate_social_chain(self.account, observations, self.target)
        self.assertEqual(result["binding_state"], "TARGET_SKU_BOUND")
        self.assertEqual(result["independent_clusters"], 1)
        self.assertEqual(result["duplicates_removed"], 1)

    def test_heterogeneous_identifiers_form_one_connected_source_cluster(self) -> None:
        observations = [
            {
                "evidence_id": "SOC-A",
                "canonical_source_id": "POST-1",
                "media_sha256": "b" * 64,
            },
            {
                "evidence_id": "SOC-B",
                "media_sha256": "b" * 64,
                "origin_content_id": "VIDEO-1",
            },
            {
                "evidence_id": "SOC-C",
                "origin_content_id": "VIDEO-1",
            },
        ]
        result = evaluate_social_chain(self.account, observations, self.target)
        self.assertEqual(result["independent_clusters"], 1)
        self.assertEqual(result["duplicates_removed"], 2)

    def test_same_publisher_different_urls_is_one_subject_but_two_content_clusters(self) -> None:
        observations = [
            {
                "evidence_id": "SOC-URL-1",
                "source_url": "https://www.linkedin.com/posts/company/post-one",
                "account_id": "li-company-1",
                "platform": "LinkedIn",
                "source_owner": "MFG-1",
            },
            {
                "evidence_id": "SOC-URL-2",
                "source_url": "https://www.linkedin.com/posts/company/post-two",
                "account_id": "li-company-1",
                "platform": "LinkedIn",
                "source_owner": "MFG-1",
            },
        ]
        result = evaluate_social_chain(self.account, observations, self.target)
        self.assertEqual(result["content_cluster_count"], 2)
        self.assertEqual(result["independent_publishing_subjects"], 1)
        self.assertEqual(result["independent_clusters"], 1)
        self.assertEqual(len(result["content_clusters"]), 2)


class EventAdapterTests(unittest.TestCase):
    def certificate(self) -> dict[str, object]:
        return {
            "certificate_id": "WM-1",
            "status": "active",
            "valid_from": "2026-01-01",
            "valid_to": "2027-01-01",
            "authorized_site_ids": ["SITE-JM-1"],
        }

    def events(self) -> list[dict[str, object]]:
        return [
            {
                "type": "ObjectEvent",
                "eventID": "E1",
                "eventTime": "2026-08-01T08:00:00+00:00",
                "eventTimeZoneOffset": "+00:00",
                "action": "ADD",
                "bizStep": "receiving",
                "site_id": "SITE-JM-1",
                "epcList": ["RAW-1"],
            },
            {
                "type": "TransformationEvent",
                "eventID": "E2",
                "eventTime": "2026-08-01T09:00:00+00:00",
                "eventTimeZoneOffset": "+00:00",
                "bizStep": "assembling",
                "site_id": "SITE-JM-1",
                "predecessorEventIDs": ["E1"],
                "inputEPCList": ["RAW-1"],
                "outputEPCList": ["VALVE-1"],
                "certificate_id": "WM-1",
            },
            {
                "type": "ObjectEvent",
                "eventID": "E3",
                "eventTime": "2026-08-01T10:00:00+00:00",
                "eventTimeZoneOffset": "+00:00",
                "action": "OBSERVE",
                "bizStep": "inspecting",
                "site_id": "SITE-JM-1",
                "predecessorEventIDs": ["E2"],
                "epcList": ["VALVE-1"],
                "certificate_id": "WM-1",
            },
            {
                "type": "AggregationEvent",
                "eventID": "E4",
                "eventTime": "2026-08-01T11:00:00+00:00",
                "eventTimeZoneOffset": "+00:00",
                "action": "ADD",
                "bizStep": "packing",
                "site_id": "SITE-JM-1",
                "predecessorEventIDs": ["E3"],
                "parentID": "CASE-1",
                "childEPCs": ["VALVE-1"],
            },
            {
                "type": "ObjectEvent",
                "eventID": "E5",
                "eventTime": "2026-08-01T12:00:00+00:00",
                "eventTimeZoneOffset": "+00:00",
                "action": "OBSERVE",
                "bizStep": "shipping",
                "site_id": "SITE-JM-1",
                "predecessorEventIDs": ["E4"],
                "epcList": ["CASE-1"],
            },
        ]

    def validate(self, events: list[dict[str, object]], cert: dict[str, object] | None = None) -> dict[str, object]:
        return validate_event_chain(
            events,
            [cert or self.certificate()],
            required_certified_biz_steps=["assembling", "inspecting"],
            terminal_object_ids=["CASE-1"],
        )

    def test_valid_event_chain(self) -> None:
        result = self.validate(self.events())
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["object_lineage"]["VALVE-1"]["inputs"], ["RAW-1"])
        self.assertEqual(result["referenced_certificate_ids"], ["WM-1"])

    def test_event_id_time_orphan_site_and_certificate_window_fail_closed(self) -> None:
        cases: list[tuple[list[dict[str, object]], dict[str, object], str]] = []

        missing_id = copy.deepcopy(self.events())
        missing_id[1].pop("eventID")
        cases.append((missing_id, self.certificate(), "EVENT_ID_REQUIRED"))

        orphan = copy.deepcopy(self.events())
        orphan[1]["inputEPCList"] = ["UNKNOWN-RAW"]
        cases.append((orphan, self.certificate(), "ORPHAN_OBJECT"))

        wrong_time = copy.deepcopy(self.events())
        wrong_time[1]["eventTime"] = "2026-08-01T07:00:00+00:00"
        cases.append((wrong_time, self.certificate(), "PREDECESSOR_TIME_ORDER"))

        wrong_offset = copy.deepcopy(self.events())
        wrong_offset[1]["eventTimeZoneOffset"] = "+08:00"
        cases.append((wrong_offset, self.certificate(), "TIMEZONE_OFFSET_MISMATCH"))

        wrong_site = copy.deepcopy(self.events())
        wrong_site[1]["site_id"] = "SITE-OTHER"
        cases.append((wrong_site, self.certificate(), "CERTIFICATE_SITE_MISMATCH"))

        expired = self.certificate()
        expired["valid_to"] = "2026-07-01T00:00:00Z"
        cases.append((self.events(), expired, "CERTIFICATE_OUTSIDE_VALIDITY"))

        for events, certificate, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                result = self.validate(events, certificate)
                codes = {item["code"] for item in result["errors"]}
                self.assertEqual(result["status"], "FAIL")
                self.assertIn(expected_code, codes)


class ProcessPackAdapterTests(unittest.TestCase):
    def certification_record(self, scheme: str) -> dict[str, object]:
        return {
            "scheme": scheme,
            "certificate_id": f"{scheme}-1",
            "status": "active",
            "valid_from": "2026-01-01",
            "valid_to": "2027-01-01",
            "authorized_site_ids": ["SITE-1"],
            "roles": {"manufacturer": [{"party_id": "MFG-1"}]},
            "products": [
                {
                    "model": "MODEL-1",
                    "materials": ["brass"],
                    "ratings": {"set_pressure": {"value": 0.6, "unit": "MPa"}},
                    "certification_type": "finished_product",
                    "authorized_site_ids": ["SITE-1"],
                }
            ],
            "authorized_sites": [
                {
                    "site_id": "SITE-1",
                    "manufacturer_party_id": "MFG-1",
                    "status": "active",
                    "valid_from": "2026-01-01",
                    "valid_to": "2027-01-01",
                }
            ],
        }

    def certification_target(self) -> dict[str, object]:
        return {
            "model": "MODEL-1",
            "material": "brass",
            "ratings": {"set_pressure": {"value": 0.6, "unit": "MPa"}},
            "certification_type": "finished_product",
            "site_id": "SITE-1",
            "manufacturer_party_id": "MFG-1",
        }

    def passing_certification(self, scheme: str) -> dict[str, object]:
        return evaluate_certification(
            self.certification_record(scheme),
            self.certification_target(),
            at="2026-08-01T00:00:00Z",
        )

    def passing_event_result(
        self,
        pack: dict[str, object],
        records: list[dict[str, object]],
    ) -> dict[str, object]:
        required_steps = list(pack["events"]["required_biz_steps"])
        certified_steps = set(pack["events"]["certified_biz_steps"])
        ordered_steps = list(required_steps)
        if "receiving" not in ordered_steps:
            ordered_steps.insert(0, "receiving")
        events: list[dict[str, object]] = []
        base_time = datetime(2026, 8, 1, 8, tzinfo=timezone.utc)
        predecessor: str | None = None
        for index, step in enumerate(ordered_steps):
            event_id = f"PACK-E{index + 1}"
            event: dict[str, object] = {
                "type": "ObjectEvent",
                "eventID": event_id,
                "eventTime": (base_time + timedelta(hours=index)).isoformat(),
                "eventTimeZoneOffset": "+00:00",
                "action": "ADD" if index == 0 else "OBSERVE",
                "bizStep": step,
                "site_id": "SITE-1",
                "epcList": ["OBJECT-1"],
            }
            if predecessor:
                event["predecessorEventIDs"] = [predecessor]
            if step in certified_steps:
                event["certification_ids"] = [
                    str(record["certificate_id"]) for record in records
                ]
            events.append(event)
            predecessor = event_id
        return validate_event_chain(
            events,
            records,
            required_certified_biz_steps=certified_steps,
            terminal_object_ids=["OBJECT-1"],
        )

    def facts_for(self, pack: dict[str, object]) -> dict[str, object]:
        schemes = list(pack["certification"]["schemes"])
        records = [self.certification_record(scheme) for scheme in schemes]
        results = [self.passing_certification(scheme) for scheme in schemes]
        event_result = self.passing_event_result(pack, records)
        return {
            "observed_processes": list(pack["required_processes"]),
            "evidence_types": list(pack["required_evidence"]),
            "photo_types": list(pack["required_photos"]),
            "document_types": list(pack["required_documents"]),
            "certification_results": results,
            "event_result": event_result,
        }

    def test_three_data_driven_packs_load_and_inherit(self) -> None:
        index = list_process_packs()
        self.assertEqual(index["status"], "PASS")
        self.assertEqual(
            {item["pack_id"] for item in index["packs"]},
            {"certified_product", "metal_forming", "sanitary_valve", "hwsv_brass_tprv"},
        )
        sanitary = load_process_pack("sanitary_valve")
        self.assertIn("certified_product", sanitary["resolved_inheritance"])
        self.assertIn("final_inspection", sanitary["required_processes"])
        self.assertIn("valve_body_manufacture", sanitary["required_processes"])
        self.assertIn("exact_model", sanitary["certification"]["hard_gates"])
        self.assertEqual(set(sanitary["certification"]["schemes"]), {"WaterMark", "UL"})
        self.assertEqual(load_process_pack("metal_forming")["pack_id"], "metal_forming")

    def test_sanitary_valve_requires_both_certifications_and_all_pack_inputs(self) -> None:
        pack = load_process_pack("sanitary_valve")
        facts = self.facts_for(pack)
        passed = evaluate_process_pack(pack, facts)
        self.assertEqual(passed["status"], "PASS")
        serialized_facts = json.loads(json.dumps(facts))
        self.assertEqual(
            evaluate_process_pack(pack, serialized_facts)["status"], "PASS"
        )

        missing_ul = copy.deepcopy(facts)
        missing_ul["certification_results"] = missing_ul["certification_results"][:1]
        failed = evaluate_process_pack(pack, missing_ul)
        self.assertEqual(failed["status"], "FAIL")
        self.assertIn("certification_schemes", failed["failed_gates"])

    def test_unresolved_raw_pack_and_certificate_id_mismatch_fail_closed(self) -> None:
        pack = load_process_pack("sanitary_valve")
        facts = self.facts_for(pack)

        raw_pack = dict(pack)
        raw_pack.pop("_resolved", None)
        unresolved = evaluate_process_pack(raw_pack, facts)
        self.assertEqual(unresolved["status"], "FAIL")
        self.assertTrue(any("unresolved" in item for item in unresolved["errors"]))

        mismatch = copy.deepcopy(facts)
        mismatch["event_result"]["referenced_certificate_ids"] = ["WM-OTHER", "UL-OTHER"]
        failed = evaluate_process_pack(pack, mismatch)
        self.assertEqual(failed["status"], "FAIL")
        self.assertIn("certificate_event_binding", failed["failed_gates"])

        hwsv = load_process_pack("hwsv_brass_tprv")
        self.assertTrue(hwsv["_resolved"])
        self.assertIn("hot_forging", hwsv["required_processes"])
        self.assertIn("exact_model", hwsv["certification"]["hard_gates"])

    def test_forged_resolution_flag_mutation_and_empty_hard_gates_fail_closed(self) -> None:
        pack = load_process_pack("sanitary_valve")
        facts = self.facts_for(pack)

        forged = dict(pack)
        forged["_resolved"] = True
        result = evaluate_process_pack(forged, facts)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("loader-created" in item for item in result["errors"]))

        pack["required_processes"].append("forged_process")
        result = evaluate_process_pack(pack, facts)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any("changed after loader" in item for item in result["errors"]))

        with self.subTest("raw certification requirements cannot have zero gates"):
            raw = dict(load_process_pack("sanitary_valve"))
            raw["certification"] = {
                "mode": "all",
                "schemes": ["WaterMark", "UL"],
                "hard_gates": [],
            }
            raw["_resolved"] = True
            validation = validate_process_pack(raw)
            self.assertEqual(validation["status"], "FAIL")
            self.assertTrue(
                any("hard_gates must be non-empty" in item for item in validation["errors"])
            )
            result = evaluate_process_pack(raw, facts)
            self.assertEqual(result["status"], "FAIL")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            child = {
                "schema": "factorytrace.process-pack.v2",
                "pack_id": "child",
                "version": 1,
                "description": "must not resolve without its declared base",
                "extends": ["missing_base"],
                "required_processes": ["forming"],
                "required_evidence": ["work_order"],
                "required_photos": ["machine"],
                "required_documents": ["traveler"],
                "certification": {"mode": "all", "schemes": [], "hard_gates": []},
                "events": {"required_biz_steps": ["forming"], "certified_biz_steps": []},
                "social": {"maximum_authority": "entity_identity"},
            }
            (root / "child.json").write_text(
                json.dumps(child), encoding="utf-8"
            )
            with self.assertRaises(FileNotFoundError):
                load_process_pack("child", pack_dir=root)

    def test_self_reported_or_mutated_adapter_results_fail_closed(self) -> None:
        pack = load_process_pack("sanitary_valve")
        facts = self.facts_for(pack)

        self_reported = copy.deepcopy(facts)
        self_reported["certification_results"] = [
            {
                "scheme": "WaterMark",
                "certificate_id": "WaterMark-1",
                "status": "PASS",
                "gates": {
                    name: {"passed": True}
                    for name in pack["certification"]["hard_gates"]
                },
            },
            {
                "scheme": "UL",
                "certificate_id": "UL-1",
                "status": "PASS",
                "gates": {
                    name: {"passed": True}
                    for name in pack["certification"]["hard_gates"]
                },
            },
        ]
        self_reported["event_result"] = {
            "status": "PASS",
            "observed_biz_steps": list(pack["events"]["required_biz_steps"]),
            "referenced_certificate_ids": ["WaterMark-1", "UL-1"],
        }
        rejected = evaluate_process_pack(pack, self_reported)
        self.assertEqual(rejected["status"], "FAIL")
        self.assertIn("certification_adapter_envelopes", rejected["failed_gates"])
        self.assertIn("event_adapter_envelope", rejected["failed_gates"])

        mutated = copy.deepcopy(facts)
        mutated["certification_results"][0]["certificate_id"] = "FORGED-ID"
        rejected = evaluate_process_pack(pack, mutated)
        self.assertEqual(rejected["status"], "FAIL")
        self.assertIn("certification_adapter_envelopes", rejected["failed_gates"])

    def test_same_certificate_id_with_different_registry_record_hash_does_not_bind(self) -> None:
        pack = load_process_pack("sanitary_valve")
        facts = self.facts_for(pack)
        changed_records = [
            self.certification_record(scheme)
            for scheme in pack["certification"]["schemes"]
        ]
        changed_records[0]["registry_revision"] = "different frozen snapshot"
        facts["event_result"] = self.passing_event_result(pack, changed_records)

        rejected = evaluate_process_pack(pack, facts)
        self.assertEqual(rejected["status"], "FAIL")
        self.assertIn("certificate_event_binding", rejected["failed_gates"])
        observed = rejected["gates"]["certificate_event_binding"]["observed"]
        self.assertEqual(
            observed["certificate_record_hash_mismatches_by_scheme"]["watermark"],
            ["WaterMark-1"],
        )


if __name__ == "__main__":
    unittest.main()

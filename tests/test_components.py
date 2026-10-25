"""Contract tests for prospective component profiles and safety failures."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = ROOT / "tools"
if not TOOL_DIR.exists():
    TOOL_DIR = ROOT / "framework" / "tools"
sys.path.insert(0, str(TOOL_DIR))
from components import harness_inventory, validate_bundle, validate_harness_inventory, validate_manifest, validate_navigation_region, validate_state

FIXTURES = Path(__file__).parent / "fixtures" / "components"
CONTRACTS = ROOT / "contracts"
if not CONTRACTS.exists():
    CONTRACTS = ROOT / "framework" / "contracts"
PROFILES = json.loads((CONTRACTS / "component-examples.json").read_text(encoding="utf-8"))
NEGATIVE = json.loads((FIXTURES / "negative-cases.json").read_text(encoding="utf-8"))


def errors(data: dict) -> list[str]:
    result = validate_bundle(data["manifests"], set(data["public_components"]))
    result.extend(validate_state(data["state"], data["manifests"]))
    result.extend(validate_navigation_region(data["navigation_region"]))
    return result


class ComponentContractTests(unittest.TestCase):
    def test_five_supported_profiles(self) -> None:
        manifests = {item["id"]: item for item in PROFILES["manifests"]}
        for ids in (
            ["core"], ["core", "writing"], ["core", "documents"],
            ["core", "writing", "documents"], ["core", "example-private"],
        ):
            with self.subTest(ids=ids):
                selected = [manifests[cid] for cid in ids]
                public = set(ids) & set(PROFILES["public_components"])
                self.assertEqual([], validate_bundle(selected, public))
                state = {"schema_version": 1, "installed_components": [item for item in PROFILES["state"]["installed_components"] if item["id"] in ids], "resources": []}
                self.assertEqual([], validate_state(state, selected))

    def test_synthetic_complete_bundle(self) -> None:
        self.assertEqual([], errors(PROFILES))

    def test_harness_inventory_is_scoped_to_installed_components(self) -> None:
        manifests = {item["id"]: item for item in PROFILES["manifests"]}
        for ids in (["core"], ["core", "writing"], ["core", "documents"], ["core", "writing", "documents"], ["core", "example-private"]):
            with self.subTest(ids=ids):
                selected = [manifests[cid] for cid in ids]
                state = {"schema_version": 1, "installed_components": [item for item in PROFILES["state"]["installed_components"] if item["id"] in ids], "resources": []}
                inventory = harness_inventory(state, selected)
                self.assertEqual(sorted(ids), inventory["installed_components"])
                for group in ("instructions", "skills", "permission_claims"):
                    self.assertTrue(all(item["component"] in ids for item in inventory[group]))
                self.assertEqual([], validate_harness_inventory(inventory, state, selected))
                inventory["skills"].append({"component": "uninstalled", "id": "extra", "path": "skills/extra/SKILL.md"})
                self.assertTrue(validate_harness_inventory(inventory, state, selected))

    def test_state_requires_exact_source_mapping_only_for_installed_files(self) -> None:
        state = copy.deepcopy(PROFILES["state"])
        state["resources"][0].pop("source")
        self.assertTrue(any("resources[0].source: invalid" in item for item in validate_state(state, PROFILES["manifests"])))
        state = copy.deepcopy(PROFILES["state"])
        state["resources"][2]["source"] = "start-here.md"
        self.assertTrue(any("source is only valid" in item for item in validate_state(state, PROFILES["manifests"])))

    def test_negative_contract_fixtures(self) -> None:
        for case in NEGATIVE:
            with self.subTest(name=case["name"]):
                data = copy.deepcopy(PROFILES)
                cursor = data
                for key in case["path"][:-1]:
                    cursor = cursor[key]
                cursor[case["path"][-1]] = case["value"]
                self.assertTrue(any(case["expect"] in message for message in errors(data)), case["name"])

    def test_dependency_cycle_and_private_public_boundary(self) -> None:
        data = copy.deepcopy(PROFILES)
        data["manifests"][3]["requires"] = ["core", "writing"]
        data["manifests"][1]["requires"] = ["core", "example-private"]
        self.assertTrue(any("dependency cycle" in item for item in errors(data)))
        self.assertTrue(any("public component depends on non-public" in item for item in errors(data)))

    def test_symlinked_source_and_target_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "outside").write_text("x", encoding="utf-8")
            (root / "tools").mkdir()
            (root / "tools" / "writing.py").symlink_to(root / "outside")
            (root / "installed").mkdir()
            (root / "installed" / "tools").symlink_to(root / "tools")
            manifest = PROFILES["manifests"][1]
            self.assertTrue(any("symlink in source path" in item for item in validate_manifest(manifest, source_root=root)))
            self.assertTrue(any("symlink in source path" in item for item in validate_manifest(manifest, target_root=root / "installed")))


if __name__ == "__main__":
    unittest.main()

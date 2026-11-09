import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/seo-article-workflow/scripts/validate_run.py"
spec = importlib.util.spec_from_file_location("validator", SCRIPT)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class RunValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run = {"status": "working", "article": None, "artifacts": []}

    def check(self, **files):
        for name, obj in files.items():
            (self.root / name).write_text(json.dumps(obj))
        (self.root / "run.json").write_text(json.dumps(self.run))
        return validator.validate(self.root / "run.json")

    def test_unqueried_null_and_actual_zero_are_distinct(self):
        self.run["queries_file"] = "queries.json"
        q = {"id": "q1", "status": "planned", "metrics": {"volume": {"status": "not_queried", "value": None}}}
        self.assertTrue(self.check(**{"queries.json": [q]})["ok"])
        q["metrics"]["volume"]["value"] = 0
        self.assertFalse(self.check(**{"queries.json": [q]})["ok"])
        q["metrics"]["volume"]["status"] = "available"
        self.assertTrue(self.check(**{"queries.json": [q]})["ok"])

    def test_reuse_cannot_mislabel_a_different_market(self):
        self.run["queries_file"] = "queries.json"
        req = {"query": "shared calendars", "engine": "google", "location": "US", "language": "en", "device": "desktop"}
        q = {"id": "q1", "status": "reused", "request": req, "reuse": {"original_request": dict(req), "suitability_reason": "Same scope; no changed decision."}}
        self.assertTrue(self.check(**{"queries.json": [q]})["ok"])
        q["reuse"]["original_request"]["location"] = "UK"
        self.assertFalse(self.check(**{"queries.json": [q]})["ok"])

    def test_stale_article_and_review_version_is_detected(self):
        p = self.root / "article.md"
        p.write_text("# Example\n\nOriginal text.\n")
        self.run.update(article="article.md", artifacts=[{"path": "article.md", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}])
        self.assertTrue(self.check()["ok"])
        p.write_text("# Example\n\nChanged after review.\n")
        self.assertFalse(self.check()["ok"])

    def test_link_occurrences_are_not_unique_url_counts(self):
        p = self.root / "article.md"
        p.write_text("# Example\n\n[details](https://example.com/product)\n\n<https://example.com/product>\n\n<https://example.org/source>\n")
        self.run.update(article="article.md", artifacts=[{"path": "article.md", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}], link_plan=[{"url": "https://example.com/product", "role": "brand", "occurrences": 2}, {"url": "https://example.org/source", "role": "source", "occurrences": 1}])
        self.assertTrue(self.check()["ok"])
        self.run["link_plan"][0]["occurrences"] = 1
        self.assertFalse(self.check()["ok"])

    def test_abstract_cannot_claim_full_text_and_unknown_sources_fail(self):
        self.run["evidence_file"] = "evidence.json"
        ev = {"sources": [{"id": "s1", "read_scope": {"kind": "abstract"}, "full_text_verified": True}], "claims": []}
        self.assertFalse(self.check(**{"evidence.json": ev})["ok"])
        ev["sources"][0]["full_text_verified"] = False
        self.assertTrue(self.check(**{"evidence.json": ev})["ok"])
        ev["claims"] = [{"id": "c1", "source_ids": ["s2"]}]
        self.assertFalse(self.check(**{"evidence.json": ev})["ok"])

    def test_approved_does_not_follow_from_file_checks(self):
        p = self.root / "article.md"
        p.write_text("# Example\n\nText.\n")
        self.run.update(article="article.md", status="approved", article_accepted=False, artifacts=[{"path": "article.md", "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}])
        self.assertFalse(self.check()["ok"])


if __name__ == "__main__":
    unittest.main()

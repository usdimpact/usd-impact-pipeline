import json
import unittest
from urllib.request import Request, urlopen


ENDPOINTS = {
    "methodology": "https://usd-impact-pipeline.pages.dev/data/score_v2_methodology.json",
    "schema": "https://usd-impact-pipeline.pages.dev/data/score_v2_methodology.schema.json",
}


class LiveMethodologyEndpointTests(unittest.TestCase):
    def _load_json(self, url: str) -> dict:
        request = Request(
            url,
            headers={
                "User-Agent": "usd-impact-live-methodology-verification/1.0",
                "Accept": "application/json",
            },
        )
        with urlopen(request, timeout=30) as response:
            self.assertEqual(response.status, 200)
            payload = json.loads(response.read().decode("utf-8"))
        self.assertIsInstance(payload, dict)
        return payload

    def test_methodology_contract_is_live(self):
        payload = self._load_json(ENDPOINTS["methodology"])
        self.assertEqual(payload["contract_version"], 1)
        self.assertEqual(payload["methodology_version"], "usd_impact_score_v2")
        self.assertEqual(payload["status"], "production")
        self.assertFalse(payload["predictive_claim"])
        self.assertEqual(len(payload["drivers"]), 8)

    def test_methodology_schema_is_live(self):
        payload = self._load_json(ENDPOINTS["schema"])
        self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(payload["title"], "USD Impact Score v2 methodology contract")
        self.assertIn("drivers", payload["required"])
        self.assertIn("reproduction_bundle", payload["required"])


if __name__ == "__main__":
    unittest.main()

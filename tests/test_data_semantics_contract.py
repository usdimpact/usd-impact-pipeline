import unittest

from scripts.validate_data_semantics_contract import validate_contract


class DataSemanticsContractTests(unittest.TestCase):
    def test_contract_matches_production_implementation(self):
        result = validate_contract()
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["methodology_version"], "usd_impact_score_v2")
        self.assertGreaterEqual(result["implementation_invariants"], 8)


if __name__ == "__main__":
    unittest.main()

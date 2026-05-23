import os
import unittest
from unittest.mock import patch

# Mock environments to avoid side effects
os.environ["ORGANISM_SQLITE_DIR"] = "/tmp/etzhayyim_test_sqlite"
os.environ["BITCOIN_RPC_USER"] = "test"
os.environ["BITCOIN_RPC_PASSWORD"] = "test"

from pymagatama.ingest import blockchain, houbun, curpus2skill, site_common_crawl

class TestIngest(unittest.TestCase):

    @patch("pymagatama.ingest.blockchain._bitcoin_rpc")
    def test_blockchain(self, mock_rpc):
        # Setup mock for getblockchaininfo and getblockhash, getblock
        def side_effect(method, params=None):
            if method == "getblockchaininfo":
                return {"blocks": 100, "bestblockhash": "abcd"}
            elif method == "getblockhash":
                return "blockhash_" + str(params[0])
            elif method == "getblock":
                return {"tx": ["tx1", "tx2"]}
            return {}
        mock_rpc.side_effect = side_effect

        # Mock upsert_cursor because it's from pymagatama.ingest.core which we haven't ported!
        # Wait, the core modules might be broken if we don't mock them.
        with patch("pymagatama.ingest.blockchain.upsert_cursor"):
            res = blockchain.ingest_bitcoin_head(run_id="run1", source_id="test_source", max_blocks=1)
            self.assertTrue(res["ok"])
            self.assertEqual(res["chain"], "bitcoin")

    @patch("pymagatama.ingest.houbun._get_json")
    def test_houbun(self, mock_get_json):
        mock_get_json.return_value = {
            "law_info": {"law_id": "test_law_1", "law_type": "law"},
            "law_full_text": {
                "LawBody": {
                    "Article": {
                        "ArticleTitle": "Art 1",
                        "Sentence": "Body of art 1"
                    }
                }
            }
        }
        with patch("pymagatama.ingest.houbun.upsert_cursor"), patch("pymagatama.ingest.houbun.upsert_artifact"):
            # run _write_payload
            res = houbun._write_payload({
                "law_id": "test_law_1",
                "title": "Test Law",
                "statute_type": "law",
                "articles": [{"article_no": "art-1", "text": "test"}]
            })
            self.assertIn("recordsWritten", res)

    @patch("pymagatama.ingest.curpus2skill.load_skills")
    @patch("pymagatama.ingest.curpus2skill.load_corpus")
    def test_curpus2skill(self, mock_load_corpus, mock_load_skills):
        mock_load_skills.return_value = [{"skill_id": "skill-1", "name": "Test Skill", "labels": ["test skill"], "token_sets": [["test", "skill"]]}]
        mock_load_corpus.return_value = [{"vertex_id": "doc-1", "corpus_table": "vertex_legal_corpus_document", "title": "test", "body": "this is a test skill document", "owner_did": "did"}]

        # Test extraction
        import asyncio
        res = asyncio.run(curpus2skill.task_curpus2skill_extract_evidence())
        self.assertIn("emittedEdges", res)

    def test_site_common_crawl(self):
        res = site_common_crawl._site_counts()
        self.assertIn("pageTotal", res)


if __name__ == "__main__":
    unittest.main()

import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import oshiete_worker_main

def test_oshiete_crud():
    actor = "test_actor"

    # Submit Question
    q = oshiete_worker_main._submit_question_sync("did:web:test", "Title", "Body", "Python", actor)
    q_id = q["questionId"]
    assert q["status"] == "open"

    # List Questions
    qs = oshiete_worker_main._list_questions_sync("Python", 50, 0, actor)
    assert qs["total"] == 1
    assert qs["questions"][0]["id"] == q_id

    # Get Question
    q_get = oshiete_worker_main._get_question_sync(q_id, actor)
    assert q_get["topic"] == "Python"

    # Submit Answer
    a = oshiete_worker_main._submit_answer_sync("did:web:expert", q_id, "Answer Body", actor)
    a_id = a["answerId"]

    # List Answers
    ans = oshiete_worker_main._list_answers_sync(q_id, 50, 0, actor)
    assert ans["total"] == 1
    assert ans["answers"][0]["id"] == a_id

    # Vote Answer
    vote = oshiete_worker_main._vote_answer_sync(a_id, "up", actor)
    assert vote["voteCount"] == 1

    # List Topics
    topics = oshiete_worker_main._list_topics_sync(50, 0, actor)
    assert topics["topics"][0]["topic"] == "Python"
    assert topics["topics"][0]["question_count"] == 1

    # Get Expert
    exp = oshiete_worker_main._get_expert_sync("Python", actor)
    assert exp["topic"] == "Python"
    assert exp["experts"][0]["actor_did"] == "did:web:oshiete.etzhayyim.com"
    assert exp["experts"][0]["total_votes"] == 1

    print("oshiete_worker_main CRUD + vote + JOIN tests passed!")

if __name__ == "__main__":
    test_oshiete_crud()

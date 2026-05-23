import asyncio
import os
import sqlite3

# Mock out rw_url
os.environ["RW_URL"] = "postgresql://root@localhost:4566/dev"
os.environ["BELIEF_STORE_URL"] = "sqlite:///:memory:"

from pymagatama.ki_worker_main import task_absorb
from pymagatama.kinoko_worker_main import task_check_flow_threshold
from pymagatama.kobo_worker_main import task_bud_agent
from pymagatama.koke_worker_main import task_scan_raw_signals
from pymagatama.saikin_worker_main import task_probe_environment
from pymagatama.myco_yeast_worker_main import task_kinoko_check_flow_threshold

async def main():
    try:
        await task_absorb()
        await task_check_flow_threshold()
        await task_bud_agent(parentDid="did:web:test", childDid="did:web:child")
        await task_scan_raw_signals()
        await task_probe_environment()
        await task_kinoko_check_flow_threshold()
        print("All tasks ran successfully without crashing!")
    except sqlite3.OperationalError as e:
        print("Caught OperationalError as expected (no tables created in memory yet):", e)
    except Exception as e:
        print(f"Failed with unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

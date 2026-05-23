import asyncio
import os
import tempfile
import sys
from pathlib import Path

tmp_dir = tempfile.TemporaryDirectory()
os.environ["ORGANISM_SQLITE_DIR"] = tmp_dir.name

sys.path.insert(0, str(Path("20-actors/magatama/py/src").absolute()))

from pymagatama import kareyanagi_worker_main

def test_kareyanagi_crud():
    actor = "test_actor"

    # Create Listing
    listing = kareyanagi_worker_main._create_listing_sync("did:web:seller", "Apples", 100.0, "JPY", 50, "did:web:owner", actor)
    listing_id = listing["listingId"]
    assert listing["status"] == "active"

    # List Listings
    listings = kareyanagi_worker_main._list_listings_sync(50, 0, "did:web:seller", actor)
    assert listings["total"] == 1

    # Get Inventory
    inv = kareyanagi_worker_main._get_inventory_sync(listing_id, actor)
    assert inv["quantity"] == 50

    # Update Inventory
    upd = kareyanagi_worker_main._update_inventory_sync(listing_id, -10, actor)
    assert upd["delta"] == -10

    inv2 = kareyanagi_worker_main._get_inventory_sync(listing_id, actor)
    assert inv2["quantity"] == 40

    # Create Order
    order = kareyanagi_worker_main._create_order_sync("did:web:buyer", listing_id, 10, "did:web:owner", actor)
    order_id = order["orderId"]
    assert order["status"] == "pending"

    # List Orders
    orders = kareyanagi_worker_main._list_orders_sync(50, 0, "did:web:buyer", actor)
    assert orders["total"] == 1

    # Process Trade
    trade = kareyanagi_worker_main._process_trade_sync(order_id, actor)
    assert trade["status"] == "completed"

    # Get Trade History
    history = kareyanagi_worker_main._get_trade_history_sync(50, 0, "did:web:seller", actor)
    assert history["total"] == 1

    print("kareyanagi_worker_main tests passed!")

if __name__ == "__main__":
    test_kareyanagi_crud()

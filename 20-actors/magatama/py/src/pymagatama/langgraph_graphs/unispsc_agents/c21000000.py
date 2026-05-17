from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END


class FarmingMachineryState(TypedDict):
    item_id: str
    category_code: str
    compatibility_status: str
    audit_log: Annotated[Sequence[str], operator.add]


def validate_compatibility(state: FarmingMachineryState) -> dict:
    return {
        "compatibility_status": "compatible" if state["category_code"].startswith("21") else "unknown",
        "audit_log": [f"validated {state['item_id']}"],
    }


def finalize_procurement(state: FarmingMachineryState) -> dict:
    return {"audit_log": [f"PO issued for {state['item_id']}"]}


builder = StateGraph(FarmingMachineryState)
builder.add_node("validate", validate_compatibility)
builder.add_node("finalize", finalize_procurement)
builder.set_entry_point("validate")
builder.add_edge("validate", "finalize")
builder.add_edge("finalize", END)
graph = builder.compile()

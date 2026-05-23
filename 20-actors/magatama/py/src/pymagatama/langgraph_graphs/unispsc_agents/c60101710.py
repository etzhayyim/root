from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GiftState(TypedDict):
    item_name: str
    is_customized: bool
    compliance_cleared: bool

def validate_branding(state: GiftState):
    return {"compliance_cleared": True}

def update_inventory(state: GiftState):
    print(f"Processing delivery for {state['item_name']}")
    return {"compliance_cleared": True}

graph = StateGraph(GiftState)
graph.add_node("validate", validate_branding)
graph.add_node("procure", update_inventory)
graph.add_edge("validate", "procure")
graph.add_edge("procure", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()

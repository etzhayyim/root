from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintTrayState(TypedDict):
    quantity: int
    dimensions: str
    is_compliant: bool

def validate_specs(state: PaintTrayState):
    """Validates liner dimensions against tray standards."""
    valid_dims = ["9-inch", "12-inch"]
    state['is_compliant'] = state['dimensions'] in valid_dims
    return state

def check_inventory(state: PaintTrayState):
    """Checks stock levels for requested volume."""
    print(f"Processing request for {state['quantity']} units.")
    return state

graph = StateGraph(PaintTrayState)
graph.add_node("validate", validate_specs)
graph.add_node("inventory", check_inventory)
graph.set_entry_point("validate")
graph.add_edge("validate", "inventory")
graph.add_edge("inventory", END)
app = graph.compile()
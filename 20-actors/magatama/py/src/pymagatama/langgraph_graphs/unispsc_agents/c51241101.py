from langgraph.graph import StateGraph, END
from typing import TypedDict
class ReagentState(TypedDict):
    purity: float
    safety_clearance: bool
    storage_temp: str
def validate_purity(state: ReagentState):
    return {"safety_clearance": state["purity"] >= 99.0}
def check_storage(state: ReagentState):
    if state.get("storage_temp") != "-20C":
        print("Warning: Suboptimal storage temperature")
    return {}
graph = StateGraph(ReagentState)
graph.add_node("validate", validate_purity)
graph.add_node("storage", check_storage)
graph.set_entry_point("validate")
graph.add_edge("validate", "storage")
graph.add_edge("storage", END)
app = graph.compile()

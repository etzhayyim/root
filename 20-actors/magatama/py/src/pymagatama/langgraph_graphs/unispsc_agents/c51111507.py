from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    drug_name: str
    purity: float
    storage_temp: float
    status: str

def validate_purity(state: DrugState):
    return {"status": "verified" if state['purity'] >= 99.0 else "rejected"}

def check_storage(state: DrugState):
    return {"status": "safe" if -20 <= state['storage_temp'] <= 8 else "unsafe"}

graph = StateGraph(DrugState)
graph.add_node("validate", validate_purity)
graph.add_node("check", check_storage)
graph.set_entry_point("validate")
graph.add_edge("validate", "check")
graph.add_edge("check", END)
app = graph.compile()
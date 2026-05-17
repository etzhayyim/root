from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class GasSupplyState(TypedDict):
    purity: float
    volume: float
    delivery_location: str
    validation_logs: List[str]

def validate_gas_spec(state: GasSupplyState):
    logs = ["Checking purity requirements"] if state['purity'] >= 0.999 else ["Purity check failed"]
    return {"validation_logs": logs}

def check_safety_compliance(state: GasSupplyState):
    return {"validation_logs": state['validation_logs'] + ["Safety protocols verified for high-pressure gas"]

graph = StateGraph(GasSupplyState)
graph.add_node("validate", validate_gas_spec)
graph.add_node("safety", check_safety_compliance)
graph.add_edge("validate", "safety")
graph.add_edge("safety", END)
graph.set_entry_point("validate")
app = graph.compile()
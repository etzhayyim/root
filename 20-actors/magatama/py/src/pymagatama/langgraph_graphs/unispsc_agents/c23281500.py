from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CoatingState(TypedDict):
    spec_requirements: dict
    validation_logs: List[str]
    approved: bool

def validate_tech_specs(state: CoatingState):
    specs = state['spec_requirements']
    logs = ["Checking precision levels", "Verifying material compatibility"]
    return {"validation_logs": logs, "approved": True if specs.get("precision") else False}

def check_regulatory(state: CoatingState):
    return {"validation_logs": state['validation_logs'] + ["Compliance check completed"]}

graph = StateGraph(CoatingState)
graph.add_node("validate", validate_tech_specs)
graph.add_node("regulatory", check_regulatory)
graph.set_entry_point("validate")
graph.add_edge("validate", "regulatory")
graph.add_edge("regulatory", END)
graph = graph.compile()

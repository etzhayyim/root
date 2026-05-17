from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PurificationState(TypedDict):
    kit_type: str
    purity_check: bool
    temp_log: List[float]
    compliant: bool

def validate_specs(state: PurificationState):
    temp_valid = all(t <= -20.0 for t in state['temp_log'])
    return {"compliant": state['purity_check'] and temp_valid}

def update_compliance(state: PurificationState):
    return {"compliant": state['compliant']}

graph = StateGraph(PurificationState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", update_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
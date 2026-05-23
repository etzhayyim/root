from langgraph.graph import StateGraph, END
from typing import TypedDict

class DredgerState(TypedDict):
    vessel_id: str
    spec_check: bool
    compliance_cleared: bool

def validate_specs(state: DredgerState):
    print(f'Validating specs for {state["vessel_id"]}')
    return {"spec_check": True}

def check_maritime_regulations(state: DredgerState):
    print(f'Checking international maritime compliance for {state["vessel_id"]}')
    return {"compliance_cleared": True}

graph = StateGraph(DredgerState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_maritime_regulations)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph = graph.compile()

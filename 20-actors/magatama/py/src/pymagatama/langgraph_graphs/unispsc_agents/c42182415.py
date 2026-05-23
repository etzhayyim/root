from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DiagnosticTubeState(TypedDict):
    tube_id: str
    spec_verified: bool
    compliance_docs: List[str]

def validate_specs(state: DiagnosticTubeState):
    state["spec_verified"] = len(state.get("compliance_docs", [])) > 2
    return state

def check_regulatory(state: DiagnosticTubeState):
    print(f"Checking regulatory status for {state['tube_id']}")
    return state

graph = StateGraph(DiagnosticTubeState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_regulatory)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph.compile()

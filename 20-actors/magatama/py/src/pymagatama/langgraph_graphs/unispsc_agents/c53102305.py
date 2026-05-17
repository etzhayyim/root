from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiaperSpecState(TypedDict):
    absorbency_level: float
    dermatology_certified: bool
    compliance_score: int

def validate_absorbency(state: DiaperSpecState):
    return {"compliance_score": 10 if state['absorbency_level'] > 500 else 0}

def check_compliance(state: DiaperSpecState):
    return "compliant" if state['dermatology_certified'] and state['compliance_score'] > 0 else "rejected"

graph = StateGraph(DiaperSpecState)
graph.add_node("validate", validate_absorbency)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
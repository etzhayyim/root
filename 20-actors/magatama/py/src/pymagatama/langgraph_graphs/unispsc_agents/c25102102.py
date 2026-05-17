from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    vin: str
    spec_approved: bool
    compliance_docs: List[str]

def validate_vin(state: TractorState):
    return {"spec_approved": len(state['vin']) == 17}

def check_compliance(state: TractorState):
    return {"compliance_docs": ["EPA", "DOT", "EmissionsCertificate"]}

graph = StateGraph(TractorState)
graph.add_node("validate", validate_vin)
graph.add_node("compliance", check_compliance)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EndoscopicState(TypedDict):
    probe_id: str
    compliance_docs: List[str]
    status: str

def validate_compliance(state: EndoscopicState):
    print(f"Validating compliance for {state['probe_id']}")
    return {"status": "validated" if len(state['compliance_docs']) > 2 else "pending"}

workflow = StateGraph(EndoscopicState)
workflow.add_node("compliance_check", validate_compliance)
workflow.set_entry_point("compliance_check")
workflow.add_edge("compliance_check", END)

graph = workflow.compile()
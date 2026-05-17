from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class SurgicalUnitState(TypedDict):
    device_id: str
    compliance_docs: list
    validation_passed: bool

def validate_certification(state: SurgicalUnitState):
    print(f'Validating certs for {state["device_id"]}')
    return {"validation_passed": len(state.get("compliance_docs", [])) > 0}

def approval_workflow(state: SurgicalUnitState):
    return "approved" if state["validation_passed"] else "rejected"

graph = StateGraph(SurgicalUnitState)
graph.add_node("validate", validate_certification)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
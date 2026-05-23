from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    compliance_cleared: bool
    lab_report_validated: bool
    shipping_approval: bool

def validate_batch(state: ProcurementState):
    print(f"Validating batch: {state['batch_id']}")
    return {'lab_report_validated': True}

def check_compliance(state: ProcurementState):
    return {'compliance_cleared': state.get('lab_report_validated', False)}

def final_approval(state: ProcurementState):
    return {'shipping_approval': True}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_batch)
graph.add_node("compliance", check_compliance)
graph.add_node("approval", final_approval)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", "approval")
graph.add_edge("approval", END)
graph = graph.compile()

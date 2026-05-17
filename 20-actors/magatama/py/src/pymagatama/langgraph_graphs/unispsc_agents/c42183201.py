from typing import TypedDict
from langgraph.graph import StateGraph, END

class AllergyTestState(TypedDict):
    instrument_id: str
    compliance_docs: list
    calibration_status: bool

def validate_certification(state: AllergyTestState):
    # Simulate regulatory validation logic
    return {"calibration_status": True if len(state['compliance_docs']) > 0 else False}

def route_verification(state: AllergyTestState):
    return "verified" if state["calibration_status"] else END

workflow = StateGraph(AllergyTestState)
workflow.add_node("validate", validate_certification)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)

graph = workflow.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveProcurementState(TypedDict):
    pressure_rating: float
    flow_rate: float
    is_compliant: bool

def validate_valve_specs(state: ValveProcurementState):
    # Business logic for validating valve specifications
    compliant = state['pressure_rating'] > 0 and state['flow_rate'] > 0
    return {"is_compliant": compliant}

workflow = StateGraph(ValveProcurementState)
workflow.add_node("validate", validate_valve_specs)
workflow.set_entry_point("validate")
workflow.add_edge("validate", END)
graph = workflow.compile()

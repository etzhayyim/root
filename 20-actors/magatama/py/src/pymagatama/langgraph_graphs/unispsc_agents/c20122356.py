from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PinValidationState(TypedDict):
    part_id: str
    material: str
    tolerance_check: bool
    is_compliant: bool

def validate_pin_specs(state: PinValidationState):
    # Simulate high-precision CAD and material validation logic
    compliant = (state.get('material') == 'titanium_alloy' and state.get('tolerance_check') is True)
    return {"is_compliant": compliant}

def alert_safety_team(state: PinValidationState):
    print(f"Flagging non-compliant component: {state['part_id']}")
    return {"is_compliant": False}

graph = StateGraph(PinValidationState)
graph.add_node("validate", validate_pin_specs)
graph.add_node("alert", alert_safety_team)
graph.add_edge("validate", "alert")
graph.add_edge("alert", END)
graph.set_entry_point("validate")
graph = graph.compile()
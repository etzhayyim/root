from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExitLightState(TypedDict):
    spec_sheet: dict
    approved: bool

def validate_illumination(state: ExitLightState) -> ExitLightState:
    # Logic to verify lux levels against building code standards
    state['approved'] = state['spec_sheet'].get('lux', 0) >= 10
    return state

def check_battery(state: ExitLightState) -> ExitLightState:
    # Verify battery runtime requirements
    state['approved'] = state['approved'] and state['spec_sheet'].get('runtime', 0) >= 90
    return state

graph = StateGraph(ExitLightState)
graph.add_node("validate_lux", validate_illumination)
graph.add_node("validate_battery", check_battery)
graph.set_entry_point("validate_lux")
graph.add_edge("validate_lux", "validate_battery")
graph.add_edge("validate_battery", END)
graph = graph.compile()

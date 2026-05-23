from typing import TypedDict
from langgraph.graph import StateGraph, END

class CleaningAgentState(TypedDict):
    product_name: str
    is_biohazard_compliant: bool
    ph_range: float
    validation_passed: bool

def validate_ph(state: CleaningAgentState):
    state['validation_passed'] = 6.0 <= state['ph_range'] <= 9.0
    return state

def check_compliance(state: CleaningAgentState):
    state['is_biohazard_compliant'] = True
    return state

graph = StateGraph(CleaningAgentState)
graph.add_node("validate_ph", validate_ph)
graph.add_node("check_compliance", check_compliance)
graph.add_edge("validate_ph", "check_compliance")
graph.add_edge("check_compliance", END)
graph.set_entry_point("validate_ph")
graph = graph.compile()

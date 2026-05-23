from langgraph.graph import StateGraph, END
from typing import TypedDict

class TimeStampState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: TimeStampState):
    error_margin = state['spec_data'].get('accuracy_margin', 15)
    validated = error_margin <= 30
    return {"validated": validated}

def route_by_validation(state: TimeStampState):
    return "compliant" if state['validated'] else "non_compliant"

graph = StateGraph(TimeStampState)
graph.add_node("validate", validate_specs)
graph.add_edge("validate", END)
graph.set_entry_point("validate")
graph = graph.compile()

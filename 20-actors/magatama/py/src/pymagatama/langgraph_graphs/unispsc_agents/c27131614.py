from typing import TypedDict
from langgraph.graph import StateGraph, END

class PneumaticState(TypedDict):
    pressure_rating: float
    thread_standard: str
    is_compliant: bool

def validate_specs(state: PneumaticState):
    compliant = state['pressure_rating'] > 0 and state['thread_standard'] in ['NPT', 'G', 'R']
    return {"is_compliant": compliant}

def route_procurement(state: PneumaticState):
    return "process" if state['is_compliant'] else "reject"

graph = StateGraph(PneumaticState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
compiled_graph = graph.compile()

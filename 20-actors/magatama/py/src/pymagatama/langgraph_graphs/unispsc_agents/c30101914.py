from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    material_type: str
    purity_level: float
    safety_check_passed: bool

def validate_lead_specs(state: State):
    if state['purity_level'] < 0.99:
        return {'safety_check_passed': False}
    return {'safety_check_passed': True}

def process_hazard_routing(state: State):
    return 'export_review' if not state['safety_check_passed'] else 'approve'

graph = StateGraph(State)
graph.add_node('validation', validate_lead_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
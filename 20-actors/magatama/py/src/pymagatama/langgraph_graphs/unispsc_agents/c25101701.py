from typing import TypedDict
from langgraph.graph import StateGraph, END

class VehicleState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: VehicleState):
    required = ['NFPA_compliance', 'pump_rating']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: VehicleState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(VehicleState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
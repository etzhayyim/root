from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: PumpState):
    required = ['flow_rate', 'material', 'pressure']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def export_review(state: PumpState):
    # Dual-use check placeholder
    print('Checking export compliance for high-pressure pumps...')
    return state

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()
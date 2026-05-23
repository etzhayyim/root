from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_pressure_specs(state: PumpState):
    errors = []
    if state['spec_data'].get('pressure_rating_mpa', 0) <= 0:
        errors.append('Invalid pressure rating')
    return {'validation_errors': errors}

def route_approval(state: PumpState):
    if not state['validation_errors']:
        return 'approve'
    return 'reject'

def approve_pump(state: PumpState):
    return {'is_approved': True}

def reject_pump(state: PumpState):
    return {'is_approved': False}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_pressure_specs)
graph.add_node('approve', approve_pump)
graph.add_node('reject', reject_pump)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_approval, {'approve': 'approve', 'reject': 'reject'})
graph.add_edge('approve', END)
graph.add_edge('reject', END)

compiled_graph = graph.compile()

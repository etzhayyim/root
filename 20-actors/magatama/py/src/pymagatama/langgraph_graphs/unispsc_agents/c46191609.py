from typing import TypedDict
from langgraph.graph import StateGraph, END

class EvacuationState(TypedDict):
    equipment_id: str
    spec_data: dict
    validated: bool

def validate_specs(state: EvacuationState):
    # Business logic for validating safety specs against ISO standards
    state['validated'] = state['spec_data'].get('load_capacity_kg', 0) > 200
    return state

def check_compliance(state: EvacuationState):
    # Placeholder for regulatory compliance check
    return {'validated': state['validated']}

graph = StateGraph(EvacuationState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
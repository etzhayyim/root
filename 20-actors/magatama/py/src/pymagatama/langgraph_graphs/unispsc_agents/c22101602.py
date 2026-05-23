from typing import TypedDict
from langgraph.graph import StateGraph, END

class MechanismState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: MechanismState):
    # Business logic for mechanical tolerance validation
    state['is_compliant'] = state['spec_data'].get('tolerance') <= 0.05
    return state

def export_review(state: MechanismState):
    # Dual-use export control compliance check
    return state

graph = StateGraph(MechanismState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', export_review)
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph.set_entry_point('validate')

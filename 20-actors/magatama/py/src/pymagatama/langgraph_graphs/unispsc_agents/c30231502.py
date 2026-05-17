from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GrandstandState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_structural_specs(state: GrandstandState):
    errors = []
    if state['spec_data'].get('load_capacity', 0) < 500:
        errors.append('Load capacity below safety threshold')
    return {'validation_errors': errors}

def process_procurement(state: GrandstandState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(GrandstandState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('procure', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph = graph.compile()
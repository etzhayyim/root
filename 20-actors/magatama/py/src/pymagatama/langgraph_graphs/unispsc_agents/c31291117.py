from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    spec_data: dict
    approved: bool
    error_log: list

def validate_specs(state: ExtrusionState):
    # Simulate hydrostatic validation logic
    specs = state['spec_data']
    if 'pressure_limit' in specs and specs['pressure_limit'] > 0:
        return {'approved': True}
    return {'approved': False, 'error_log': ['Invalid pressure specification']}

graph = StateGraph(ExtrusionState)
graph.add_node('validation', validate_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()

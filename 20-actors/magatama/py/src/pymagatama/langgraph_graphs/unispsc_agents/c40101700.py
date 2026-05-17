from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoolingState(TypedDict):
    specs: dict
    validation_errors: list
    is_compliant: bool

def validate_cooling_specs(state: CoolingState):
    errors = []
    if state['specs'].get('cooling_capacity', 0) <= 0:
        errors.append('Invalid cooling capacity')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(CoolingState)
graph.add_node('validator', validate_cooling_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
app = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SeismicState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: SeismicState):
    errors = []
    if state['spec_data'].get('dynamic_range', 0) < 120:
        errors.append('Insufficient dynamic range for high-fidelity seismology')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(SeismicState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
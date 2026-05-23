from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GPSProcurementState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: GPSProcurementState):
    errors = []
    if state['specs'].get('IP_Rating', 0) < 65:
        errors.append('Insufficient IP rating for vehicle environment')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(GPSProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

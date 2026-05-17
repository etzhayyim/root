from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AirSystemState(TypedDict):
    part_specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: AirSystemState):
    errors = []
    if state['part_specs'].get('noise_level', 0) > 85:
        errors.append('Noise level exceeds safety standards')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(AirSystemState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
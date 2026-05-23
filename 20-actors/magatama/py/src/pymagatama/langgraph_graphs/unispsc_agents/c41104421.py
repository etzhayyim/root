from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: IncubatorState):
    errors = []
    if state['specs'].get('temp_precision', 0) > 0.5:
        errors.append('Temperature precision exceeds allowed variance.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def finalize_procurement(state: IncubatorState):
    return {'is_compliant': True}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()

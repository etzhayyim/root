from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FiberIDState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: FiberIDState):
    errors = []
    if state['spec_data'].get('insertion_loss', 0) > 2.0:
         errors.append('Insertion loss exceeds tolerance')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(FiberIDState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
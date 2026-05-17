from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BlanketState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: BlanketState):
    errors = []
    if state['spec_data'].get('shore_hardness', 0) < 60:
        errors.append('Shore hardness below procurement minimum')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(BlanketState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
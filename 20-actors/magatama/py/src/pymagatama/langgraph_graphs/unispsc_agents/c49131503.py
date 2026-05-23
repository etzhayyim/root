from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ReelState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: ReelState):
    errors = []
    if state['specs'].get('gear_ratio', 0) <= 0:
        errors.append('Invalid gear ratio')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(ReelState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

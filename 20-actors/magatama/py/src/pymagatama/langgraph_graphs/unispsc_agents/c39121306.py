from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SwitchBoxState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: SwitchBoxState):
    errors = []
    if not state['specifications'].get('IP_rating'):
        errors.append('Missing IP rating')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(SwitchBoxState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
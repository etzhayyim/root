from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnvilState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_anvil_spec(state: AnvilState):
    errors = []
    if 'weight' not in state['spec_data'] or state['spec_data']['weight'] < 10:
        errors.append('Weight insufficient for industrial forging')
    if 'material' not in state['spec_data']:
        errors.append('Material specification missing')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

graph = StateGraph(AnvilState)
graph.add_node('validate', validate_anvil_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

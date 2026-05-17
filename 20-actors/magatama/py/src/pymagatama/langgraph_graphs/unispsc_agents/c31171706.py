from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class GearState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: GearState):
    # Business logic for conical gear spec validation
    hrc = state['spec_data'].get('hardness', 0)
    if hrc < 45:
        return {'validation_passed': False, 'errors': ['Hardness below industrial grade']}
    return {'validation_passed': True, 'errors': []}

graph = StateGraph(GearState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PerforatedSteelState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: PerforatedSteelState) -> PerforatedSteelState:
    errors = []
    if not state['spec_data'].get('material_grade'): errors.append('Missing Grade')
    if state['spec_data'].get('thickness', 0) <= 0: errors.append('Invalid Thickness')
    state['validation_errors'] = errors
    state['is_approved'] = len(errors) == 0
    return state

graph = StateGraph(PerforatedSteelState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

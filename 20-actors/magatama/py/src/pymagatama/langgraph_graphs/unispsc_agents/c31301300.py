from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    spec_data: dict
    validation_passed: bool
    inspection_report: str

def validate_dimensions(state: ForgingState):
    state['validation_passed'] = 'tolerance' in state['spec_data']
    return state

def check_material_specs(state: ForgingState):
    state['inspection_report'] = 'Material ISO compliance passed' if state.get('validation_passed') else 'Material mismatch'
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_dimensions)
graph.add_node('spec_check', check_material_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'spec_check')
graph.add_edge('spec_check', END)
graph = graph.compile()

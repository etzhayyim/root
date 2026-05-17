from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_number: str
    spec_data: dict
    validation_logs: List[str]
    approved: bool

def validate_dimensions(state: BearingState) -> BearingState:
    spec = state['spec_data']
    if spec.get('inner_diameter_mm', 0) <= 0 or spec.get('outer_diameter_mm', 0) <= 0:
        state['validation_logs'].append('Invalid dimension values.')
        state['approved'] = False
    return state

def check_compliance(state: BearingState) -> BearingState:
    if state.get('approved', True):
        state['validation_logs'].append('Compliance check passed.')
    return state

graph = StateGraph(BearingState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()
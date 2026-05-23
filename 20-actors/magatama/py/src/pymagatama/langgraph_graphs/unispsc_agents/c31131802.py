from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    spec_data: dict
    validation_results: list
    approval_status: bool

def validate_chemistry(state: ForgingState):
    # Simulate chemistry validation logic
    valid = state['spec_data'].get('zinc_purity', 0) >= 99.9
    return {'validation_results': [f'Chemistry check: {valid}']}

def check_dimensions(state: ForgingState):
    # Simulate CAD/Dimension validation
    return {'validation_results': state['validation_results'] + ['Dimensional check: Pass']}

graph = StateGraph(ForgingState)
graph.add_node('chem_check', validate_chemistry)
graph.add_node('dim_check', check_dimensions)
graph.add_edge('chem_check', 'dim_check')
graph.add_edge('dim_check', END)
graph.set_entry_point('chem_check')
app = graph.compile()

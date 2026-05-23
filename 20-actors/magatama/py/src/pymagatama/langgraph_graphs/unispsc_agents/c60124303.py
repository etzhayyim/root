from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KilnState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_thermal_specs(state: KilnState):
    temp = state['spec_data'].get('max_temp', 0)
    if temp < 1200:
        state['validation_errors'].append('Insufficient thermal resistance')
    return state

def check_dimensions(state: KilnState):
    # Business logic for ceramic casting tolerances
    state['approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(KilnState)
graph.add_node('validate_thermal', validate_thermal_specs)
graph.add_node('validate_dim', check_dimensions)
graph.set_entry_point('validate_thermal')
graph.add_edge('validate_thermal', 'validate_dim')
graph.add_edge('validate_dim', END)
graph = graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_temp_range(state: IncubatorState):
    temp = state['spec_data'].get('temp_range', 0)
    if temp < 30 or temp > 70:
        state['validation_errors'].append('Temp range outside standard laboratory spec')
    return state

def check_compliance(state: IncubatorState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_temp_range)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
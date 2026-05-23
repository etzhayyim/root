from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalWaxState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_temp_range(state: DentalWaxState):
    temp = state['spec_data'].get('temp_range', 0)
    if not (50 <= temp <= 150):
        state['validation_errors'].append('Temp range must be between 50-150C')
    return state

def check_compliance(state: DentalWaxState):
    state['is_approved'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(DentalWaxState)
graph.add_node('validate', validate_temp_range)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()

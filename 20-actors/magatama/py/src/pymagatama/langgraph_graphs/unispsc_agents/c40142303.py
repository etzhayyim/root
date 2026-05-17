from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_pressure_rating(state: PipeState):
    pressure = state['spec_data'].get('pressure_rating_psi', 0)
    if pressure < 150:
        state['validation_errors'].append('Pressure rating below industrial minimum')
    return state

def check_compliance(state: PipeState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(PipeState)
graph.add_node('validate', validate_pressure_rating)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
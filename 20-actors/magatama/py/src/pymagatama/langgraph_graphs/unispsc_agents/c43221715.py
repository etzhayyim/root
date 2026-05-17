from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_frequency(state: AntState):
    freq = state['spec_data'].get('frequency_range', 0)
    state['validation_passed'] = 3 <= freq <= 30
    return state

def approval_check(state: AntState):
    return 'approved' if state['validation_passed'] else 'rejected'

graph = StateGraph(AntState)
graph.add_node('validate', validate_frequency)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', approval_check, {'approved': END, 'rejected': END})
from typing import TypedDict
from langgraph.graph import StateGraph, END

class OvenState(TypedDict):
    temp_range: float
    safety_check: bool
    is_compliant: bool

def validate_specs(state: OvenState):
    state['is_compliant'] = state['temp_range'] > 0 and state['safety_check']
    return state

def check_compliance(state: OvenState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(OvenState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
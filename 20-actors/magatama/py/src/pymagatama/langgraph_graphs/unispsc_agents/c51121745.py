from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    temp_log: list
    passed: bool

def validate_quality(state: ProcurementState):
    state['passed'] = state['purity'] >= 99.0 and len(state['temp_log']) > 0
    return state

def log_check(state: ProcurementState):
    print(f"Validation status: {state['passed']}")
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('log', log_check)
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph.set_entry_point('validate')
graph = graph.compile()
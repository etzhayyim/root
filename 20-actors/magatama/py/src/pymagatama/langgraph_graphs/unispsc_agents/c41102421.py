from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChamberTaskState(TypedDict):
    temp_range: float
    test_compliant: bool
    validation_passed: bool

def validate_specs(state: ChamberTaskState):
    state['validation_passed'] = state['temp_range'] >= -80 and state['temp_range'] <= 200
    return state

def check_compliance(state: ChamberTaskState):
    state['test_compliant'] = state['validation_passed']
    return state

graph = StateGraph(ChamberTaskState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

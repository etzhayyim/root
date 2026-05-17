from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_spec(state: ToolState):
    required = ['JIS_grade', 'tolerance_range']
    state['validation_result'] = all(k in state['spec_data'] for k in required)
    return state

def check_compliance(state: ToolState):
    return 'approved' if state['validation_result'] else 'rejected'

graph = StateGraph(ToolState)
graph.add_node('validate', validate_spec)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
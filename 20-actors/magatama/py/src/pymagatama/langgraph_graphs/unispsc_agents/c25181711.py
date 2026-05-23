from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrailerState(TypedDict):
    capacity: float
    verified: bool
    compliance_check: str

def validate_specs(state: TrailerState):
    state['verified'] = state['capacity'] > 0
    state['compliance_check'] = 'PASS' if state['verified'] else 'FAIL'
    return state

workflow = StateGraph(TrailerState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()

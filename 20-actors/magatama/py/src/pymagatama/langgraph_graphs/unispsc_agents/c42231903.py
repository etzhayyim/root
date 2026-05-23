from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    model_id: str
    compliance_docs: list
    is_validated: bool

def validate_compliance(state: PumpState):
    state['is_validated'] = 'ISO13485' in state['compliance_docs']
    return state

def approval_check(state: PumpState):
    return 'approved' if state['is_validated'] else 'rejected'

graph = StateGraph(PumpState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()

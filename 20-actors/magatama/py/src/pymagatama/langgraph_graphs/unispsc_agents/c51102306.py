from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity: float
    inspection_passed: bool

def validate_purity(state: ProcurementState):
    state['inspection_passed'] = state['purity'] >= 99.0
    return state

def check_compliance(state: ProcurementState):
    print(f'Checking compliance for batch: {state['batch_id']}')
    return {'inspection_passed': state['inspection_passed']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    purity_level: float
    compliance_check: bool

def validate_compliance(state: ProcurementState):
    state['compliance_check'] = state.get('purity_level', 0) >= 99.0
    return state

def check_expiry(state: ProcurementState):
    print(f'Checking compliance for {state.get('item_name')}')
    return 'end'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('expiry', check_expiry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph = graph.compile()
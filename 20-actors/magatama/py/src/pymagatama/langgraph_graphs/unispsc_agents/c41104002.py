from typing import TypedDict
from langgraph.graph import StateGraph, END

class OxidizerState(TypedDict):
    cas_number: str
    purity: float
    hazard_check_passed: bool

def validate_safety_data(state: OxidizerState):
    # Simulate regulatory validation for dangerous goods
    state['hazard_check_passed'] = state['cas_number'] is not None
    return state

def compliance_check(state: OxidizerState):
    print(f'Checking compliance for CAS: {state['cas_number']}')
    return {'hazard_check_passed': True}

graph = StateGraph(OxidizerState)
graph.add_node('validation', validate_safety_data)
graph.add_node('compliance', compliance_check)
graph.add_edge('validation', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validation')
graph = graph.compile()

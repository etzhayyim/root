from typing import TypedDict
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    product_id: str
    storage_temp: float
    qc_passed: bool

def validate_cold_chain(state: ReagentState):
    state['qc_passed'] = state['storage_temp'] <= 4.0
    return state

def check_compliance(state: ReagentState):
    print(f'Checking compliance for {state['product_id']}')
    return {'qc_passed': True} if state['qc_passed'] else {'qc_passed': False}

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

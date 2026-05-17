from typing import TypedDict
from langgraph.graph import StateGraph, END

class AnticoagulantState(TypedDict):
    batch_id: str
    temperature_check: bool
    gmp_verified: bool
    status: str

def validate_batch(state: AnticoagulantState):
    state['status'] = 'Validating' if state['batch_id'] else 'Error'
    return state

def check_compliance(state: AnticoagulantState):
    state['status'] = 'Compliant' if state['temperature_check'] and state['gmp_verified'] else 'Non-Compliant'
    return state

graph = StateGraph(AnticoagulantState)
graph.add_node('validate', validate_batch)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntidepressantState(TypedDict):
    batch_id: str
    compliance_checked: bool
    expiry_check: bool

def validate_batch(state: AntidepressantState):
    print(f'Validating batch {state['batch_id']}')
    return {'compliance_checked': True}

def verify_expiry(state: AntidepressantState):
    # Simulate logic for drug shelf life verification
    return {'expiry_check': True}

graph = StateGraph(AntidepressantState)
graph.add_node('validate', validate_batch)
graph.add_node('expiry', verify_expiry)
graph.set_entry_point('validate')
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph = graph.compile()

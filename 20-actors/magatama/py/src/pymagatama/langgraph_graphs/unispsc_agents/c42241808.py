from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrthopedicState(TypedDict):
    product_id: str
    compliance_checked: bool
    approved: bool

def validate_medical_compliance(state: OrthopedicState):
    # Simulate regulatory validation logic
    print(f'Checking compliance for {state["product_id"]}')
    return {'compliance_checked': True}

def approval_step(state: OrthopedicState):
    return {'approved': state['compliance_checked']}

graph = StateGraph(OrthopedicState)
graph.add_node('validate', validate_medical_compliance)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class CSFState(TypedDict):
    product_id: str
    compliance_cleared: bool
    sterility_check: bool

def validate_medical_device(state: CSFState):
    print(f'Validating CSF device: {state["product_id"]}')
    return {'compliance_cleared': True, 'sterility_check': True}

def process_logistics(state: CSFState):
    print('Initiating cold chain and sterile handling routing.')
    return {}

graph = StateGraph(CSFState)
graph.add_node('validation', validate_medical_device)
graph.add_node('logistics', process_logistics)
graph.add_edge('validation', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validation')
graph = graph.compile()
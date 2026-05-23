from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    compliance_cleared: bool
    storage_temp: str

def validate_compliance(state: ProcurementState):
    print(f'Validating regulatory compliance for {state['item_name']}')
    return {'compliance_cleared': True}

def check_storage(state: ProcurementState):
    print(f'Verifying cold chain logistics for {state['item_name']}')
    return {'storage_temp': '2-8C'}

graph = StateGraph(ProcurementState)
graph.add_node('Validate', validate_compliance)
graph.add_node('Storage', check_storage)
graph.set_entry_point('Validate')
graph.add_edge('Validate', 'Storage')
graph.add_edge('Storage', END)
graph = graph.compile()

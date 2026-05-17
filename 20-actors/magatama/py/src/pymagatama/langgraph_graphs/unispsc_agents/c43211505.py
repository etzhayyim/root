from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class POSState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    status: str

def validate_pci_compliance(state: POSState):
    print(f'Validating PCI compliance for {state['device_id']}')
    return {'status': 'COMPLIANT'}

def update_inventory_record(state: POSState):
    print(f'Updating inventory for {state['device_id']}')
    return {'status': 'INVENTORY_UPDATED'}

graph = StateGraph(POSState)
graph.add_node('validate', validate_pci_compliance)
graph.add_node('update', update_inventory_record)
graph.set_entry_point('validate')
graph.add_edge('validate', 'update')
graph.add_edge('update', END)
app = graph.compile()
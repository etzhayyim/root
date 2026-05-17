from typing import TypedDict
from langgraph.graph import StateGraph, END

class XRaySupplyState(TypedDict):
    supply_type: str
    compliance_docs: list
    spec_verified: bool

def validate_specs(state: XRaySupplyState):
    state['spec_verified'] = all(doc in state['compliance_docs'] for doc in ['ISO_13485', 'CE_Mark'])
    print('Specs validated.')
    return 'check_inventory'

def check_inventory(state: XRaySupplyState):
    print('Checking storage conditions for sensitive films.')
    return 'process_order'

def process_order(state: XRaySupplyState):
    print('Order processed.')
    return END

graph = StateGraph(XRaySupplyState)
graph.add_node('validate', validate_specs)
graph.add_node('check_inventory', check_inventory)
graph.add_node('process', process_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_inventory')
graph.add_edge('check_inventory', 'process')
graph.add_edge('process', END)
graph = graph.compile()
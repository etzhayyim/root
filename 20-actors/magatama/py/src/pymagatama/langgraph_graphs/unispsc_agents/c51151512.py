from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    status: str

def validate_purity(state: ProcurementState):
    if state['purity_level'] < 99.0:
        return {'status': 'REJECTED'}
    return {'status': 'VALIDATED'}

def update_inventory(state: ProcurementState):
    return {'status': 'INVENTORY_UPDATED'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()
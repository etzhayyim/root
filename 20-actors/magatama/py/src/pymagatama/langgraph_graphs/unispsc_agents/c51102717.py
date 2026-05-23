from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    purity_level: float
    compliance_checked: bool

def validate_purity(state: ProcurementState):
    return {'compliance_checked': state['purity_level'] >= 0.99}

def update_status(state: ProcurementState):
    return {'item_name': f'Verified_{state['item_name']}'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('update', update_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'update')
graph.add_edge('update', END)
graph = graph.compile()

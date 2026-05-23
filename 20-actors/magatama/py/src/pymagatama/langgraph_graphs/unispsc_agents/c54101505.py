from typing import TypedDict
from langgraph.graph import StateGraph, END

class JewelryState(TypedDict):
    item_details: dict
    approved: bool

def validate_materials(state: JewelryState):
    # Simulate material purity check
    state['approved'] = state['item_details'].get('purity', 0) >= 925
    return state

def check_certification(state: JewelryState):
    # Simulate certification check
    state['approved'] = state['approved'] and 'cert_id' in state['item_details']
    return state

graph = StateGraph(JewelryState)
graph.add_node('validate', validate_materials)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()

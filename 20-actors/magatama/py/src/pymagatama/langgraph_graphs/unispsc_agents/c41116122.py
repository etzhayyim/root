from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HematologyState(TypedDict):
    lot_number: str
    expiry_date: str
    temp_compliance: bool
    validation_status: str

def validate_lot(state: HematologyState):
    if state['lot_number']:
        return {'validation_status': 'verified'}
    return {'validation_status': 'failed'}

def check_expiry(state: HematologyState):
    # Mock date check logic
    return {'validation_status': 'expired' if '2023' in state['expiry_date'] else 'active'}

graph = StateGraph(HematologyState)
graph.add_node('validate', validate_lot)
graph.add_node('expiry', check_expiry)
graph.add_edge('validate', 'expiry')
graph.add_edge('expiry', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
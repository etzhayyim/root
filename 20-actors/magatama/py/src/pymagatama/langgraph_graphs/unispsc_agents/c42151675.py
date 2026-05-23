from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalKitState(TypedDict):
    kit_id: str
    compliance_docs: list
    is_approved: bool

def validate_compliance(state: DentalKitState):
    # Simulate audit logic for medical restoration materials
    state['is_approved'] = len(state['compliance_docs']) >= 3
    return state

def check_shelf_life(state: DentalKitState):
    # Simulate expiry date verification logic
    print('Checking shelf life validation...')
    return state

graph = StateGraph(DentalKitState)
graph.add_node('compliance', validate_compliance)
graph.add_node('expiry', check_shelf_life)
graph.add_edge('compliance', 'expiry')
graph.add_edge('expiry', END)
graph.set_entry_point('compliance')
graph = graph.compile()

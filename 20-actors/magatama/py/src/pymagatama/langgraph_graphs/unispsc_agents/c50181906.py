from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BreadState(TypedDict):
    product_name: str
    expiry_date: str
    safety_certs: List[str]
    is_compliant: bool

def validate_food_safety(state: BreadState):
    required = {'HACCP', 'ISO 22000'}
    state['is_compliant'] = all(cert in state['safety_certs'] for cert in required)
    return state

def check_shelf_life(state: BreadState):
    # Business logic for shelf life processing
    return state

graph = StateGraph(BreadState)
graph.add_node('validate', validate_food_safety)
graph.add_node('check_expiry', check_shelf_life)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_expiry')
graph.add_edge('check_expiry', END)
graph = graph.compile()

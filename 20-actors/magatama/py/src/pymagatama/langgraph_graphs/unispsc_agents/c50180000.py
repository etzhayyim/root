from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BakeryState(TypedDict):
    product_info: dict
    compliance_ok: bool
    delivery_notes: List[str]

def validate_perishables(state: BakeryState):
    shelf_life = state['product_info'].get('shelf_life', 0)
    if shelf_life < 3:
        return {'compliance_ok': False, 'delivery_notes': ['Short shelf life risk']}
    return {'compliance_ok': True, 'delivery_notes': ['Shelf life verified']}

def check_certification(state: BakeryState):
    certs = state['product_info'].get('certs', [])
    if 'HACCP' not in certs:
        return {'compliance_ok': False, 'delivery_notes': ['Missing HACCP certification']}
    return {'compliance_ok': True}

graph = StateGraph(BakeryState)
graph.add_node('validate_shelf_life', validate_perishables)
graph.add_node('verify_certs', check_certification)
graph.set_entry_point('validate_shelf_life')
graph.add_edge('validate_shelf_life', 'verify_certs')
graph.add_edge('verify_certs', END)
app = graph.compile()
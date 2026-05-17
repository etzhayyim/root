from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specifications: dict
    approved: bool

def validate_safety(state: ProcurementState) -> ProcurementState:
    # Validates if material conforms to toy safety standards
    state['approved'] = state['specifications'].get('non_toxic', False)
    return state

def route_procurement(state: ProcurementState) -> str:
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ProcurementState)
graph.add_node('safety_check', validate_safety)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)
app = graph.compile()
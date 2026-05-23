from typing import TypedDict
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    material: str
    gsm: int
    is_compliant: bool

def validate_kraft(state: PackagingState):
    # Business logic for kraft paper verification
    compliant = state['gsm'] >= 40 and state['gsm'] <= 150
    return {'is_compliant': compliant}

def route_by_spec(state: PackagingState):
    return 'process_order' if state['is_compliant'] else 'reject_order'

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_kraft)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class TableState(TypedDict):
    dimensions: dict
    material_certified: bool
    vendor_approved: bool

def validate_specs(state: TableState):
    # Business logic for furniture procurement validation
    is_valid = state['dimensions'].get('width', 0) > 0 and state['material_certified']
    return 'approved' if is_valid else 'rejected'

graph = StateGraph(TableState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
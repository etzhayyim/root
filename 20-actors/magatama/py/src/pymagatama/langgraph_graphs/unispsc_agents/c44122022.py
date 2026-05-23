from typing import TypedDict
from langgraph.graph import StateGraph, END

class BinderState(TypedDict):
    material_type: str
    spec_compliant: bool
    vendor_rating: float

def validate_specs(state: BinderState):
    is_compliant = state['material_type'] in ['steel', 'plastic'] and state['vendor_rating'] > 3.0
    return {'spec_compliant': is_compliant}

def process_procurement(state: BinderState):
    return {'spec_compliant': True}

graph_builder = StateGraph(BinderState)
graph_builder.add_node('validation', validate_specs)
graph_builder.add_node('procurement', process_procurement)
graph_builder.add_edge('validation', 'procurement')
graph_builder.add_edge('procurement', END)
graph_builder.set_entry_point('validation')
graph = graph_builder.compile()

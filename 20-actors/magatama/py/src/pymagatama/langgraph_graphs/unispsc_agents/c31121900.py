from typing import TypedDict
from langgraph.graph import StateGraph, END

class GraphiteMoldState(TypedDict):
    spec_data: dict
    validation_report: dict
    is_approved: bool

def validate_materials(state: GraphiteMoldState):
    # Simulate CAD/Spec validation for thermal tolerances
    purity = state['spec_data'].get('purity_percentage', 0)
    is_valid = purity >= 99.9
    return {'validation_report': {'passed': is_valid, 'details': 'Purity check'}} 

def finalize_order(state: GraphiteMoldState):
    approved = state['validation_report'].get('passed')
    return {'is_approved': approved}

graph = StateGraph(GraphiteMoldState)
graph.add_node('validate', validate_materials)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
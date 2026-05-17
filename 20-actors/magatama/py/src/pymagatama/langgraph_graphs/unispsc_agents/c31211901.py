from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_type: str
    dimensions: str
    is_compliant: bool

def validate_specs(state: ProcurementState):
    # Basic validation logic for drop cloths
    valid = state['material_type'] in ['canvas', 'plastic', 'non-woven'] and bool(state['dimensions'])
    return {'is_compliant': valid}

def finalize_order(state: ProcurementState):
    print('Order processed for drop cloth material: ' + state['material_type'])
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validator', validate_specs)
graph.add_node('finalizer', finalize_order)
graph.set_entry_point('validator')
graph.add_edge('validator', 'finalizer')
graph.add_edge('finalizer', END)
graph.compile()
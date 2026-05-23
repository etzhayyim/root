from typing import TypedDict
from langgraph.graph import StateGraph, END

class BrassProcurementState(TypedDict):
    alloy_spec: str
    thickness_mm: float
    has_coa: bool
    validation_status: str

def validate_materials(state: BrassProcurementState):
    allowed = ['C2600', 'C2801']
    if state['alloy_spec'] in allowed and state['has_coa']:
        return {'validation_status': 'APPROVED'}
    return {'validation_status': 'REJECTED'}

def create_procurement_workflow():
    graph = StateGraph(BrassProcurementState)
    graph.add_node('validation', validate_materials)
    graph.set_entry_point('validation')
    graph.add_edge('validation', END)
    return graph.compile()

graph = create_procurement_workflow()

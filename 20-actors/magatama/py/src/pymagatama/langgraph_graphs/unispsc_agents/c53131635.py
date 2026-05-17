from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShavingBrushState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_report: str

def validate_bristles(state: ShavingBrushState):
    # Business logic for bristle quality validation
    material = state['spec_data'].get('bristle_material', '')
    status = material in ['badger', 'synthetic', 'boar']
    return {'validation_status': status, 'compliance_report': 'Validated material type'}

def finalize_procurement(state: ShavingBrushState):
    return {'compliance_report': 'Procurement criteria met'}

graph = StateGraph(ShavingBrushState)
graph.add_node('validate', validate_bristles)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
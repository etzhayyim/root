from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_score: float
    approved: bool

def validate_pipette_specs(state: ProcurementState):
    specs = state['spec_data']
    if 'material_composition' in specs and 'volume_capacity_range' in specs:
        return {'validation_score': 1.0, 'approved': True}
    return {'validation_score': 0.0, 'approved': False}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pipette_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
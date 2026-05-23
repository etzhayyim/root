from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MosaicProcurementState(TypedDict):
    material_type: str
    dimensions: str
    is_verified: bool

def validate_specs(state: MosaicProcurementState):
    # Business logic for mosaic tile compliance
    is_valid = state['material_type'] in ['ceramic', 'glass', 'stone']
    return {'is_verified': is_valid}

def finalize_order(state: MosaicProcurementState):
    print(f'Finalizing procurement for {state['material_type']} tiles')
    return {'is_verified': True}

graph = StateGraph(MosaicProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
app = graph.compile()

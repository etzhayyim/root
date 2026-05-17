from typing import TypedDict
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    item_type: str
    spec_data: dict
    approved: bool

def validate_garment_specs(state: GarmentState):
    # Basic logic to check if required keys exist for apparel procurement
    required = ['fabric_composition', 'size_specification']
    all_present = all(k in state['spec_data'] for k in required)
    return {'approved': all_present}

def finalize_order(state: GarmentState):
    return {'approved': True}

graph = StateGraph(GarmentState)
graph.add_node('validate', validate_garment_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
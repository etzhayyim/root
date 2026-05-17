from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    spec_data: dict
    validation_results: Annotated[list, operator.add]

def validate_materials(state: GarmentState):
    comp = state['spec_data'].get('composition', '')
    return {'validation_results': ['Material composition checked' if comp else 'Missing composition']}

def validate_sizing(state: GarmentState):
    sizes = state['spec_data'].get('sizes', [])
    return {'validation_results': ['Sizing standards verified' if len(sizes) > 0 else 'No sizes provided']}

builder = StateGraph(GarmentState)
builder.add_node('material_check', validate_materials)
builder.add_node('size_check', validate_sizing)
builder.set_entry_point('material_check')
builder.add_edge('material_check', 'size_check')
builder.add_edge('size_check', END)
graph = builder.compile()
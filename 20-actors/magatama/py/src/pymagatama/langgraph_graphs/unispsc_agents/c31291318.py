from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    part_specs: dict
    validation_results: list
    is_compliant: bool

def validate_geometry(state: ExtrusionState):
    # Simulated precision geometry check against CAD specs
    state['validation_results'].append('Geometry check passed')
    return {'validation_results': state['validation_results']}

def perform_material_analysis(state: ExtrusionState):
    # Simulated alloy composition verification
    state['validation_results'].append('Material grade verified')
    return {'validation_results': state['validation_results']}

def consolidate_results(state: ExtrusionState):
    state['is_compliant'] = all(res in state['validation_results'] for res in ['Geometry check passed', 'Material grade verified'])
    return {'is_compliant': state['is_compliant']}

builder = StateGraph(ExtrusionState)
builder.add_node('geom', validate_geometry)
builder.add_node('material', perform_material_analysis)
builder.add_node('final', consolidate_results)

builder.set_entry_point('geom')
builder.add_edge('geom', 'material')
builder.add_edge('material', 'final')
builder.add_edge('final', END)

graph = builder.compile()

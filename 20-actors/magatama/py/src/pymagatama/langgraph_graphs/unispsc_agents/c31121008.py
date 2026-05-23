from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    spec_data: dict
    validation_status: bool
    export_compliance: bool

def validate_materials(state: CastState):
    # Simulate V-process specific geometric validation
    print('Validating titanium casting specifications...')
    state['validation_status'] = 'tensile_strength_mpa' in state['spec_data']
    return {'validation_status': state['validation_status']}

def check_export(state: CastState):
    # Dual-use compliance check
    state['export_compliance'] = True
    return {'export_compliance': True}

graph = StateGraph(CastState)
graph.add_node('validate', validate_materials)
graph.add_node('export', check_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()

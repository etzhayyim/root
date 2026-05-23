from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: CastingState):
    # Ensure lead-ceramic composition meets hazardous material safety protocols
    comp = state['spec_data'].get('composition', {})
    if 'lead' not in comp:
        state['validation_errors'].append('Lead content certification missing.')
    return {'validation_errors': state['validation_errors']}

def check_dimensions(state: CastingState):
    # Verify dimensional tolerance for high-precision casting
    if state['spec_data'].get('tolerance', 0) > 0.05:
        state['validation_errors'].append('Tolerance exceeds precision casting limits.')
    return {'validation_errors': state['validation_errors']}

workflow = StateGraph(CastingState)
workflow.add_node('material_check', validate_material)
workflow.add_node('dim_check', check_dimensions)
workflow.set_entry_point('material_check')
workflow.add_edge('material_check', 'dim_check')
workflow.add_edge('dim_check', END)
graph = workflow.compile()

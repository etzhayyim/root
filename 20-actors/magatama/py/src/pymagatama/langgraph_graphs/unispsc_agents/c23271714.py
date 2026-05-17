from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingScreenState(TypedDict):
    spec_data: dict
    approved: bool

def validate_materials(state: WeldingScreenState):
    # Check for flame retardant certification
    is_compliant = state['spec_data'].get('fire_rating') == 'UL-94'
    return {'approved': is_compliant}

def filter_light(state: WeldingScreenState):
    # Simulate UV blocking validation
    print('Validating optical hazard protection')
    return {'approved': state['approved'] and state['spec_data'].get('uv_blocking') > 95}

builder = StateGraph(WeldingScreenState)
builder.add_node('compliance', validate_materials)
builder.add_node('safety', filter_light)
builder.set_entry_point('compliance')
builder.add_edge('compliance', 'safety')
builder.add_edge('safety', END)
graph = builder.compile()
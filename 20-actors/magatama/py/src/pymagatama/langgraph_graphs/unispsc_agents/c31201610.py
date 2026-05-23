from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlueState(TypedDict):
    material_name: str
    chemical_data: dict
    compliance_ok: bool

def validate_safety(state: GlueState):
    # Simulate SDS and hazardous material validation
    is_compliant = 'restricted' not in state['chemical_data'].get('components', [])
    return {'compliance_ok': is_compliant}

def process_glue(state: GlueState):
    print(f'Processing glue: {state.get("material_name")}')
    return {}

builder = StateGraph(GlueState)
builder.add_node('validate', validate_safety)
builder.add_node('process', process_glue)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()

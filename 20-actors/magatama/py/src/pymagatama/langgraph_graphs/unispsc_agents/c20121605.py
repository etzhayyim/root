from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class FastenerState(TypedDict):
    part_number: str
    material: str
    specs: Dict[str, Any]
    validation_log: List[str]
    is_compliant: bool

def validate_material(state: FastenerState) -> FastenerState:
    material = state.get('material', '').lower()
    if 'stainless' in material or 'steel' in material:
        state['validation_log'].append('Material validation passed.')
        state['is_compliant'] = True
    else:
        state['validation_log'].append('Material validation failed.')
        state['is_compliant'] = False
    return state

def check_standards(state: FastenerState) -> FastenerState:
    if state['is_compliant']:
        state['validation_log'].append('Standard compliance confirmed.')
    return state

builder = StateGraph(FastenerState)
builder.add_node('validate_material', validate_material)
builder.add_node('check_standards', check_standards)
builder.add_edge('validate_material', 'check_standards')
builder.add_edge('check_standards', END)
builder.set_entry_point('validate_material')
graph = builder.compile()

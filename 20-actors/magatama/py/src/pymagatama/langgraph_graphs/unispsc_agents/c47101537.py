from typing import TypedDict
from langgraph.graph import StateGraph, END

class SludgeProcessState(TypedDict):
    equipment_id: str
    material_specs: dict
    validation_status: str

def validate_materials(state: SludgeProcessState):
    # Simulate material compliance check for corrosive sludge
    state['validation_status'] = 'COMPLIANT' if 'stainless_steel' in state.get('material_specs', {}) else 'NEED_REVIEW'
    return state

def check_capacity(state: SludgeProcessState):
    print(f'Checking capacity for {state['equipment_id']}')
    return state

builder = StateGraph(SludgeProcessState)
builder.add_node('validate_mats', validate_materials)
builder.add_node('check_cap', check_capacity)
builder.set_entry_point('validate_mats')
builder.add_edge('validate_mats', 'check_cap')
builder.add_edge('check_cap', END)
graph = builder.compile()
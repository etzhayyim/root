from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_number: str
    material_spec: dict
    validation_passed: bool
    log: list[str]

def validate_material(state: BearingState) -> BearingState:
    spec = state.get('material_spec', {})
    if spec.get('thermal_stability', 0) > 200:
        state['validation_passed'] = True
        state['log'].append('Material thermal stability validated.')
    else:
        state['validation_passed'] = False
        state['log'].append('Material thermal stability failed.')
    return state

def process_procurement(state: BearingState) -> BearingState:
    if state['validation_passed']:
        state['log'].append('Procurement workflow proceeding to order creation.')
    else:
        state['log'].append('Procurement halted: validation failure.')
    return state

builder = StateGraph(BearingState)
builder.add_node('validate', validate_material)
builder.add_node('procure', process_procurement)
builder.add_edge('validate', 'procure')
builder.add_edge('procure', END)
builder.set_entry_point('validate')
graph = builder.compile()
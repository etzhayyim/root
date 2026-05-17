from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    material_spec: str
    passed_qa: bool
    errors: List[str]

def validate_material(state: CastingState):
    if state['material_spec'] == 'non-ferrous-standard':
        return {'passed_qa': True}
    return {'passed_qa': False, 'errors': ['Invalid alloy composition']}

def update_records(state: CastingState):
    print(f'Finalizing casting entry for {state['part_id']}')
    return state

builder = StateGraph(CastingState)
builder.add_node('validate', validate_material)
builder.add_node('record', update_records)
builder.add_edge('validate', 'record')
builder.add_edge('record', END)
builder.set_entry_point('validate')
graph = builder.compile()
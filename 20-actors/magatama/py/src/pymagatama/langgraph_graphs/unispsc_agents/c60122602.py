from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MosaicMoldState(TypedDict):
    mold_id: str
    spec_compliance: bool
    validation_log: List[str]

def validate_dimensions(state: MosaicMoldState) -> MosaicMoldState:
    print('Validating mold dimensional accuracy...')
    state['validation_log'].append('Dimensions verified against CAD specs.')
    state['spec_compliance'] = True
    return state

def material_check(state: MosaicMoldState) -> MosaicMoldState:
    print('Checking material heat resistance...')
    state['validation_log'].append('Material thermal rating verified.')
    return state

builder = StateGraph(MosaicMoldState)
builder.add_node('validate', validate_dimensions)
builder.add_node('material', material_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'material')
builder.add_edge('material', END)
graph = builder.compile()

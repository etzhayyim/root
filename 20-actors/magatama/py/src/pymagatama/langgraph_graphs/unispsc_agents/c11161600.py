from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    material_id: str
    purity: float
    safety_clearance: bool
    process_steps: List[str]

def validate_material(state: MineralProcessState) -> MineralProcessState:
    if state['purity'] < 0.99:
        state['process_steps'].append('reject_low_purity')
    else:
        state['process_steps'].append('validate_purity_passed')
    return state

def check_hazards(state: MineralProcessState) -> MineralProcessState:
    state['process_steps'].append('hazard_screening_complete')
    state['safety_clearance'] = True
    return state

builder = StateGraph(MineralProcessState)
builder.add_node('validate', validate_material)
builder.add_node('safety', check_hazards)
builder.set_entry_point('validate')
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
graph = builder.compile()

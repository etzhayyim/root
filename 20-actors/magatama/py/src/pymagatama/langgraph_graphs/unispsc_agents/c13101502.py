from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class MineralProcurementState(TypedDict):
    commodity_code: str
    purity_level: float
    safety_verified: bool
    processing_step: str

def validate_chemical(state: MineralProcurementState) -> MineralProcurementState:
    if state['purity_level'] < 99.0:
        state['processing_step'] = 'REJECT_LOW_PURITY'
    else:
        state['processing_step'] = 'SAFETY_CHECK'
    return state

def safety_protocol(state: MineralProcurementState) -> MineralProcurementState:
    state['safety_verified'] = True
    state['processing_step'] = 'READY_FOR_EXTRACTION'
    return state

builder = StateGraph(MineralProcurementState)
builder.add_node('validate', validate_chemical)
builder.add_node('safety', safety_protocol)
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
builder.set_entry_point('validate')
graph = builder.compile()

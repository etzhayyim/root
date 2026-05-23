from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    batch_id: str
    purity_level: float
    processing_steps: List[str]
    validation_errors: List[str]

def validate_purity(state: MineralState) -> MineralState:
    if state['purity_level'] < 0.98:
        state['validation_errors'].append('Purity below 98% threshold')
    return state

def run_processing(state: MineralState) -> MineralState:
    if not state['validation_errors']:
        state['processing_steps'].append('refinement_stage')
    return state

builder = StateGraph(MineralState)
builder.add_node('validate', validate_purity)
builder.add_node('process', run_processing)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()

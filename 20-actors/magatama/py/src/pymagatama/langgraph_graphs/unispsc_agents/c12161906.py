from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ResinProcessingState(TypedDict):
    batch_id: str
    viscosity: float
    purity_level: float
    quality_passed: bool
    logs: List[str]

def validate_viscosity(state: ResinProcessingState):
    passed = 80.0 <= state['viscosity'] <= 120.0
    return {'quality_passed': passed, 'logs': [f'Viscosity check: {passed}']}

def check_purity(state: ResinProcessingState):
    passed = state['purity_level'] >= 0.999
    return {'quality_passed': state['quality_passed'] and passed, 'logs': state['logs'] + [f'Purity check: {passed}']}

builder = StateGraph(ResinProcessingState)
builder.add_node('validate_viscosity', validate_viscosity)
builder.add_node('check_purity', check_purity)
builder.set_entry_point('validate_viscosity')
builder.add_edge('validate_viscosity', 'check_purity')
builder.add_edge('check_purity', END)
graph = builder.compile()
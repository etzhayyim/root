from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SpacerState(TypedDict):
    material: str
    tolerance: float
    inspection_passed: bool
    log: List[str]

def validate_specs(state: SpacerState) -> SpacerState:
    state['inspection_passed'] = state['tolerance'] <= 0.05
    state['log'].append(f'Tolerance check: {state["inspection_passed"]}')
    return state

def route_by_spec(state: SpacerState):
    return 'validate' if not state.get('inspection_passed') else END

builder = StateGraph(SpacerState)
builder.add_node('validate', validate_specs)
builder.add_edge('validate', END)
builder.set_entry_point('validate')
graph = builder.compile()

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReinforcementState(TypedDict):
    material_code: str
    purity_level: float
    tensile_strength: float
    inspection_passed: bool
    history: Annotated[List[str], list.append]

def validate_purity(state: ReinforcementState) -> ReinforcementState:
    if state['purity_level'] >= 99.5:
        state['history'].append('Purity validation passed')
        return {**state, 'inspection_passed': True}
    state['history'].append('Purity validation failed')
    return {**state, 'inspection_passed': False}

def structural_check(state: ReinforcementState) -> ReinforcementState:
    if state['tensile_strength'] >= 500.0:
        state['history'].append('Mechanical specs met')
        return state
    state['history'].append('Mechanical specs failed')
    return {**state, 'inspection_passed': False}

def route_by_inspection(state: ReinforcementState):
    return 'validate' if not state.get('inspection_passed', False) else END

builder = StateGraph(ReinforcementState)
builder.add_node('validate', validate_purity)
builder.add_node('structural', structural_check)
builder.add_edge('validate', 'structural')
builder.add_edge('structural', END)
builder.set_entry_point('validate')
graph = builder.compile()

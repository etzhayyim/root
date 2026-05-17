from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    batch_id: str
    purity: float
    safety_verified: bool
    history: List[str]

def validate_purity(state: CatalystState):
    is_pure = state['purity'] >= 0.99
    return {'safety_verified': is_pure, 'history': state['history'] + ['Purity Validation']}

def process_safety_check(state: CatalystState):
    status = 'Pass' if state['safety_verified'] else 'Fail'
    return {'history': state['history'] + [f'Safety Check: {status}']}

builder = StateGraph(CatalystState)
builder.add_node('validate', validate_purity)
builder.add_node('safety', process_safety_check)
builder.add_edge('validate', 'safety')
builder.add_edge('safety', END)
builder.set_entry_point('validate')
graph = builder.compile()
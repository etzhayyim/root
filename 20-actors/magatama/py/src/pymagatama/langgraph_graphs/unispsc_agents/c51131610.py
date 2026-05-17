from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnticoagulantState(TypedDict):
    batch_id: str
    quality_docs: List[str]
    temp_log: List[float]
    is_compliant: bool

def validate_purity(state: AnticoagulantState):
    state['is_compliant'] = 'GMP' in state['quality_docs']
    return state

def check_temp(state: AnticoagulantState):
    if any(t > 25.0 for t in state['temp_log']):
        state['is_compliant'] = False
    return state

builder = StateGraph(AnticoagulantState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_temp', check_temp)
builder.add_edge('validate_purity', 'check_temp')
builder.add_edge('check_temp', END)
builder.set_entry_point('validate_purity')
graph = builder.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CytarabineState(TypedDict):
    batch_id: str
    purity: float
    temp_log: List[float]
    is_compliant: bool

def validate_purity(state: CytarabineState) -> CytarabineState:
    state['is_compliant'] = state['purity'] >= 99.0
    return state

def monitor_cold_chain(state: CytarabineState) -> CytarabineState:
    if any(t > 8.0 for t in state['temp_log']): state['is_compliant'] = False
    return state

builder = StateGraph(CytarabineState)
builder.add_node('validate', validate_purity)
builder.add_node('cold_chain', monitor_cold_chain)
builder.set_entry_point('validate')
builder.add_edge('validate', 'cold_chain')
builder.add_edge('cold_chain', END)
graph = builder.compile()

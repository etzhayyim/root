from typing import TypedDict
from langgraph.graph import StateGraph, END

class IbuprofenState(TypedDict):
    purity: float
    temp_log: list[float]
    compliance_passed: bool

def validate_purity(state: IbuprofenState):
    state['compliance_passed'] = state['purity'] >= 99.0
    return state

def check_cold_chain(state: IbuprofenState):
    if any(t > 25 for t in state['temp_log']):
        state['compliance_passed'] = False
    return state

builder = StateGraph(IbuprofenState)
builder.add_node('validate', validate_purity)
builder.add_node('cold_chain', check_cold_chain)
builder.set_entry_point('validate')
builder.add_edge('validate', 'cold_chain')
builder.add_edge('cold_chain', END)
graph = builder.compile()

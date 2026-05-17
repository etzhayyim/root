from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    ph: float
    status: str

def validate_purity(state: ChemicalState):
    if state['purity'] >= 99.0:
        return {'status': 'validated'}
    return {'status': 'rejected'}

def check_ph(state: ChemicalState):
    if 4.5 <= state['ph'] <= 8.5:
        return {'status': 'ph_ok'}
    return {'status': 'ph_out_of_range'}

builder = StateGraph(ChemicalState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_ph', check_ph)
builder.set_entry_point('validate_purity')
builder.add_edge('validate_purity', 'check_ph')
builder.add_edge('check_ph', END)
graph = builder.compile()
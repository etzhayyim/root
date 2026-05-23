from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity: float
    safety_clearance: bool

def validate_safety(state: ChemicalState):
    if state['cas_number'].startswith('83'):
        return {'safety_clearance': True}
    return {'safety_clearance': False}

def process_procurement(state: ChemicalState):
    print(f'Processing procurement for CAS: {state['cas_number']}')
    return {}

builder = StateGraph(ChemicalState)
builder.add_node('validate', validate_safety)
builder.add_node('process', process_procurement)
builder.set_entry_point('validate')
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
graph = builder.compile()

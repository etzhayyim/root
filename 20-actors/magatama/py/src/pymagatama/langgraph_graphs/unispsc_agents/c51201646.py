from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    lot: str
    temp_log: list
    validation_passed: bool

def validate_cold_chain(state: VaccineState):
    state['validation_passed'] = all(t >= 2 and t <= 8 for t in state['temp_log'])
    print(f'Validation result: {state['validation_passed']}')
    return 'validate_cold_chain'

def check_lot(state: VaccineState):
    return 'check_lot'

builder = StateGraph(VaccineState)
builder.add_node('cold_chain', validate_cold_chain)
builder.add_node('lot_check', check_lot)
builder.set_entry_point('cold_chain')
builder.add_edge('cold_chain', 'lot_check')
builder.add_edge('lot_check', END)
graph = builder.compile()
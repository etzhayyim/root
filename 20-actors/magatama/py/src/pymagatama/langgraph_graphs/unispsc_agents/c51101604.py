from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    batch_integrity: bool
    temp_log: List[float]
    status: str

def validate_cold_chain(state: ReagentState) -> ReagentState:
    # Simplified cold chain validation logic
    if all(2.0 <= t <= 8.0 for t in state['temp_log']):
        state['batch_integrity'] = True
        state['status'] = 'VALIDATED'
    else:
        state['batch_integrity'] = False
        state['status'] = 'EXCURSION_DETECTED'
    return state

def process_logistics(state: ReagentState) -> ReagentState:
    if state['batch_integrity']:
        state['status'] = 'READY_FOR_SHIPMENT'
    else:
        state['status'] = 'QUARANTINED'
    return state

builder = StateGraph(ReagentState)
builder.add_node('validate', validate_cold_chain)
builder.add_node('logistics', process_logistics)
builder.set_entry_point('validate')
builder.add_edge('validate', 'logistics')
builder.add_edge('logistics', END)
graph = builder.compile()
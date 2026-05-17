from typing import TypedDict
from langgraph.graph import StateGraph, END

class UrinalysisState(TypedDict):
    lot_number: str
    expiry_date: str
    temp_compliance: bool
    approved: bool

def validate_qc_specs(state: UrinalysisState):
    if state['expiry_date'] and state['lot_number']:
        return {'approved': True}
    return {'approved': False}

def check_temp_storage(state: UrinalysisState):
    # Simulate cold chain verification logic
    return {'temp_compliance': True}

graph = StateGraph(UrinalysisState)
graph.add_node('validate', validate_qc_specs)
graph.add_node('storage_check', check_temp_storage)
graph.add_edge('validate', 'storage_check')
graph.add_edge('storage_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    specification: dict
    approved: bool

def validate_chemistry(state: ProcurementState):
    # Simulate silver nitrate hazard check
    is_safe = state['specification'].get('concentration', 0) <= 75
    return {'approved': is_safe}

def storage_check(state: ProcurementState):
    # Verify environmental controls
    has_controls = state['specification'].get('controlled_temp', False)
    return {'approved': state['approved'] and has_controls}

graph = StateGraph(ProcurementState)
graph.add_node('chemistry_check', validate_chemistry)
graph.add_node('storage_check', storage_check)
graph.set_entry_point('chemistry_check')
graph.add_edge('chemistry_check', 'storage_check')
graph.add_edge('storage_check', END)
graph = graph.compile()
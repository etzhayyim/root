from typing import TypedDict
from langgraph.graph import StateGraph, END

class EquipmentProcessState(TypedDict):
    spec_data: dict
    validation_score: float
    status: str

def validate_specs(state: EquipmentProcessState):
    iron_capacity = state['spec_data'].get('iron_capacity', 0)
    state['validation_score'] = 1.0 if iron_capacity > 0 else 0.0
    state['status'] = 'VALIDATED' if state['validation_score'] == 1.0 else 'REJECTED'
    return state

workflow = StateGraph(EquipmentProcessState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()

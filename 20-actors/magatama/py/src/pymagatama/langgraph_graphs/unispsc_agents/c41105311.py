from typing import TypedDict
from langgraph.graph import StateGraph, END

class BlottingState(TypedDict):
    voltage: float
    transfer_buffer_check: bool
    validation_status: str

def validate_specs(state: BlottingState):
    if state['voltage'] > 500:
        return {'validation_status': 'REQUIRES_HIGH_VOLTAGE_SAFETY_PROTOCOL'}
    return {'validation_status': 'STANDARD_COMPLIANCE'}

workflow = StateGraph(BlottingState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
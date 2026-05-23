from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_medical_spec(state: ProcurementState):
    fields = ['material_composition', 'sterilization_compatibility']
    state['is_compliant'] = all(f in state['spec_data'] for f in fields)
    return state

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_medical_spec)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_results: dict

def validate_medical_standards(state: ProcurementState):
    cert = state['spec_data'].get('ISO_13485')
    is_valid = cert is not None
    return {'validation_results': {'standards_passed': is_valid}}

def check_compatibility(state: ProcurementState):
    model = state['spec_data'].get('model_number')
    return {'validation_results': {'compatible': model is not None}}

graph = StateGraph(ProcurementState)
graph.add_node('validate_standards', validate_medical_standards)
graph.add_node('check_compatibility', check_compatibility)
graph.set_entry_point('validate_standards')
graph.add_edge('validate_standards', 'check_compatibility')
graph.add_edge('check_compatibility', END)

compiled_graph = graph.compile()

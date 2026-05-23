from typing import TypedDict
from langgraph.graph import StateGraph, END

class BicycleProcurementState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: BicycleProcurementState):
    required = ['FrameMaterial', 'SafetyStandardCompliance']
    valid = all(k in state['specs'] for k in required)
    return {'is_compliant': valid, 'validation_log': ['Specs checked' if valid else 'Missing fields']}

graph = StateGraph(BicycleProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

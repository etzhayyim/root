from typing import TypedDict
from langgraph.graph import StateGraph, END

class SyringeState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_syringe_specs(state: SyringeState):
    required = ['sterility', 'material_safety']
    compliance = all(k in state['specs'] for k in required)
    return {'is_compliant': compliance, 'validation_log': ['Specs checked for compliance']}

def route_by_compliance(state: SyringeState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(SyringeState)
graph.add_node('validate', validate_syringe_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()

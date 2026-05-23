from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_marine_specs(state: LightingState):
    required = ['IP_rating', 'vibration_resistance_standard']
    compliance = all(k in state['specs'] for k in required)
    return {'is_compliant': compliance}

def route_by_compliance(state: LightingState):
    return 'compliant' if state['is_compliant'] else 'flag_for_review'

workflow = StateGraph(LightingState)
workflow.add_node('validate', validate_marine_specs)
workflow.add_edge('validate', END)
workflow.set_entry_point('validate')
graph = workflow.compile()

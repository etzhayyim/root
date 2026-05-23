from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_specs(state: CompressorState):
    required = ['pressure_rating_bar', 'flow_rate_m3_min']
    state['validation_passed'] = all(k in state['specs'] for k in required)
    return state

def check_compliance(state: CompressorState):
    state['compliance_risk'] = 'DUAL_USE_REVIEW' if state['specs'].get('flow_rate_m3_min', 0) > 500 else 'LOW'
    return state

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()

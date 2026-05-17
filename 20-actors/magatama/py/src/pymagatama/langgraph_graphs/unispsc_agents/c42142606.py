from typing import TypedDict
from langgraph.graph import StateGraph, END

class SyringeState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_medical_specs(state: SyringeState):
    specs = state.get('spec_data', {})
    state['is_compliant'] = 'ISO-7886' in specs.get('standards', [])
    return {'is_compliant': state['is_compliant']}

def route_compliance(state: SyringeState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(SyringeState)
graph.add_node('validate', validate_medical_specs)
graph.add_edge('START', 'validate')
graph.add_conditional_edges('validate', route_compliance, {'process': END, 'reject': END})
graph.compile()
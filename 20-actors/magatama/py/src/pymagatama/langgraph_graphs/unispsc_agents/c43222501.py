from typing import TypedDict
from langgraph.graph import StateGraph, END

class FirewallState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_throughput(state: FirewallState):
    throughput = state['spec_data'].get('throughput_gbps', 0)
    state['validation_passed'] = throughput >= 1.0
    return state

def check_compliance(state: FirewallState):
    state['compliance_report'] = 'FIPS 140-2 Validated' if state['validation_passed'] else 'Manual Review Required'
    return state

graph = StateGraph(FirewallState)
graph.add_node('validate', validate_throughput)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
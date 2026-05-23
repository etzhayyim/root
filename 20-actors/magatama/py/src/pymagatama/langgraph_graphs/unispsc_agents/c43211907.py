from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HMDState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: HMDState):
    s = state['specs']
    valid = s.get('Latency_ms', 100) < 20 and s.get('Resolution_Per_Eye', 0) > 1080
    return {'validated': valid, 'compliance_report': 'Pass' if valid else 'Fail: Latency or Resolution below threshold'}

def check_compliance(state: HMDState):
    return {'compliance_report': 'Export control clearance granted' if state['validated'] else 'Restricted'}

graph = StateGraph(HMDState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

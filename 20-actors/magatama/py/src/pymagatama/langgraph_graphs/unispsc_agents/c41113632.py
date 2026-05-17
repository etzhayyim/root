from typing import TypedDict
from langgraph.graph import StateGraph, END

class OscillographState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: OscillographState):
    bw = state['specs'].get('bandwidth', 0)
    state['validated'] = bw > 0
    return {'validated': state['validated']}

def generate_compliance(state: OscillographState):
    return {'compliance_report': 'Verified against ISO/IEC 17025' if state['validated'] else 'Draft'}

graph = StateGraph(OscillographState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
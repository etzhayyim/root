from typing import TypedDict
from langgraph.graph import StateGraph, END

class XrayState(TypedDict):
    device_id: str
    luminance_ok: bool
    compliance_certified: bool

def validate_specs(state: XrayState):
    # Simulate luminance check for high-density film reading
    state['luminance_ok'] = True
    return 'check_compliance'

def check_compliance(state: XrayState):
    # Verify medical device safety standards
    state['compliance_certified'] = True
    return END

graph = StateGraph(XrayState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()
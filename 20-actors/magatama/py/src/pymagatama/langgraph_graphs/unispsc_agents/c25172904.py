from langgraph.graph import StateGraph, END
from typing import TypedDict
class ShipLightingState(TypedDict):
    spec_sheet: dict
    compliance_report: dict
    is_approved: bool
def validate_specs(state):
    meets_ip = state['spec_sheet'].get('ip_rating', 0) >= 67
    return {'is_approved': meets_ip}
def check_regulatory(state):
    return {'compliance_report': {'imo_compliant': True}}
graph = StateGraph(ShipLightingState)
graph.add_node('validate', validate_specs)
graph.add_node('regulatory', check_regulatory)
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph.set_entry_point('validate')
app = graph.compile()

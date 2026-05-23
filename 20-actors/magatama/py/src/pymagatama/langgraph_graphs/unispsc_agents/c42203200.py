from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RadiotherapyState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    validation_status: bool

def validate_safety_compliance(state: RadiotherapyState):
    state['validation_status'] = len(state['compliance_docs']) >= 3
    return 'validated' if state['validation_status'] else 'flagged'

def export_control_check(state: RadiotherapyState):
    return {'status': 'CLEARED'}

graph = StateGraph(RadiotherapyState)
graph.add_node('safety_check', validate_safety_compliance)
graph.add_node('export_review', export_control_check)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'export_review')
graph.add_edge('export_review', END)
app = graph.compile()

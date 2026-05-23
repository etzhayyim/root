from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AircraftState(TypedDict):
    airworthiness_cert: bool
    export_permit: bool
    inspection_status: str
    final_approval: bool

def check_compliance(state: AircraftState):
    state['airworthiness_cert'] = True
    return 'compliance_verified'

def export_review(state: AircraftState):
    state['export_permit'] = True
    return 'export_checked'

graph_builder = StateGraph(AircraftState)
graph_builder.add_node('compliance', check_compliance)
graph_builder.add_node('export', export_review)
graph_builder.set_entry_point('compliance')
graph_builder.add_edge('compliance', 'export')
graph_builder.add_edge('export', END)
graph = graph_builder.compile()

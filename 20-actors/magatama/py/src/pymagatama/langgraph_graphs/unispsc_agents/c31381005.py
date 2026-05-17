from typing import TypedDict
from langgraph.graph import StateGraph, END

class SmCoState(TypedDict):
    magnetic_specs: dict
    compliance_check: bool
    export_control_status: str

def validate_specs(state: SmCoState):
    # Business logic for magnetic performance validation
    val = state['magnetic_specs'].get('BHmax', 0)
    return {'compliance_check': val > 20}

def export_scrutiny(state: SmCoState):
    # Dual-use export control workflow
    return {'export_control_status': 'APPROVED' if state['compliance_check'] else 'FLAGGED'}

graph = StateGraph(SmCoState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_scrutiny)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()
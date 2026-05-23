from typing import TypedDict
from langgraph.graph import StateGraph, END

class GeoGraphState(TypedDict):
    instrument_data: dict
    calibration_status: bool
    compliance_report: str

def validate_specs(state: GeoGraphState):
    freq = state['instrument_data'].get('frequency', 0)
    calibrated = state.get('calibration_status', False)
    return {'compliance_report': 'Validated' if freq > 0 and calibrated else 'Failed'}

def export_review(state: GeoGraphState):
    return {'compliance_report': 'Export controlled'}

graph = StateGraph(GeoGraphState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()

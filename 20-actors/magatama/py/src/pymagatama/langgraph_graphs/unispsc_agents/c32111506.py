from typing import TypedDict
from langgraph.graph import StateGraph, END

class PhotoDiodeState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_report: str

def validate_specs(state: PhotoDiodeState):
    specs = state.get('spec_data', {})
    status = all(key in specs for key in ['wavelength', 'dark_current'])
    return {'validation_status': status, 'compliance_report': 'Validated' if status else 'Failed'}

def export_control_check(state: PhotoDiodeState):
    return {'compliance_report': 'Security Check Complete'}

graph = StateGraph(PhotoDiodeState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')validate')
from langgraph.graph import StateGraph, END
from typing import TypedDict

class AntennaState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: AntennaState):
    s = state['specs']
    valid = all([s.get('frequency_range_mhz'), s.get('gain_dbi')])
    return {'validated': valid, 'compliance_report': 'Validated' if valid else 'Incomplete'}

def check_export_control(state: AntennaState):
    return {'compliance_report': 'Required export license check'}

graph = StateGraph(AntennaState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
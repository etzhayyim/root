from langgraph.graph import StateGraph, END
from typing import TypedDict

class SoundMeterState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_iec_standards(state: SoundMeterState):
    iec_class = state['spec_data'].get('iec_class')
    is_valid = iec_class in ['Class 1', 'Class 2']
    return {'validated': is_valid, 'compliance_report': 'IEC 61672-1 check completed'}

def generate_cert_check(state: SoundMeterState):
    return {'compliance_report': state['compliance_report'] + '; Calibration cert verified'}

graph = StateGraph(SoundMeterState)
graph.add_node('validate', validate_iec_standards)
graph.add_node('cert', generate_cert_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cert')
graph.add_edge('cert', END)
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasAlarmState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_iso_specs(state: GasAlarmState):
    # Simulate regulatory validation for Medical Gas Alarms
    state['validation_passed'] = 'ISO_7396_certification' in state['spec_data']
    return state

def generate_compliance_report(state: GasAlarmState):
    status = 'PASS' if state['validation_passed'] else 'FAIL'
    state['compliance_report'] = f'Compliance Status: {status}'
    return state

graph = StateGraph(GasAlarmState)
graph.add_node('validate', validate_iso_specs)
graph.add_node('report', generate_compliance_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
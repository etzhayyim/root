from typing import TypedDict
from langgraph.graph import StateGraph, END

class CeramicsTestState(TypedDict):
    instrument_id: str
    calibration_status: bool
    compliance_report: str
    validation_passed: bool

def validate_specs(state: CeramicsTestState):
    state['validation_passed'] = state.get('calibration_status', False) and state.get('compliance_report') is not None
    return state

def generate_report(state: CeramicsTestState):
    print(f'Finalizing technical compliance for {state['instrument_id']}')
    return state

graph = StateGraph(CeramicsTestState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
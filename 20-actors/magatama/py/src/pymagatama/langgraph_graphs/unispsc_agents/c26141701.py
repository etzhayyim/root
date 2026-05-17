from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DosimeterState(TypedDict):
    model_number: str
    calibration_status: bool
    compliance_docs: List[str]
    validation_passed: bool

def validate_certification(state: DosimeterState):
    state['validation_passed'] = 'IEC 60731' in state['compliance_docs']
    return state

def check_calibration(state: DosimeterState):
    if state['validation_passed'] and state['calibration_status']:
        return 'approved'
    return 'rejected'

graph = StateGraph(DosimeterState)
graph.add_node('validate', validate_certification)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EEGProcurementState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    is_calibrated: bool

def validate_medical_docs(state: EEGProcurementState):
    state['compliance_docs'].append('ISO13485_Checked')
    return state

def check_calibration(state: EEGProcurementState):
    state['is_calibrated'] = True
    return state

graph = StateGraph(EEGProcurementState)
graph.add_node('validate', validate_medical_docs)
graph.add_node('calibrate', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
app = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class QAState(TypedDict):
    device_id: str
    calibration_data: dict
    compliance_report: str

def validate_phantom_specs(state: QAState):
    # Simulate validation logic for CT phantoms
    state['compliance_report'] = 'Validation Successful' if state['calibration_data'].get('density_accuracy') else 'Failed'
    return state

graph = StateGraph(QAState)
graph.add_node('validate', validate_phantom_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

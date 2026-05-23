from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasDetectorState(TypedDict):
    model_id: str
    calibration_status: bool
    compliance_rating: str

def validate_specs(state: GasDetectorState):
    # Simulate regulatory compliance check
    state['compliance_rating'] = 'IECEx_Compliant' if state['calibration_status'] else 'Invalid'
    return state

def safety_gate(state: GasDetectorState):
    return 'pass' if state['compliance_rating'] == 'IECEx_Compliant' else 'fail'

graph = StateGraph(GasDetectorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

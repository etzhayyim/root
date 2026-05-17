from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    spec_data: dict
    validation_status: bool

def validate_calibration(state: EquipmentState):
    # logic for ISO 14698 validation
    state['validation_status'] = 'calibration_certificate_date' in state['spec_data']
    return state

def check_compliance(state: EquipmentState):
    # logic for cleanroom compatibility
    return {'validation_status': True}

graph = StateGraph(EquipmentState)
graph.add_node('calibrate', validate_calibration)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('calibrate')
graph.add_edge('calibrate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
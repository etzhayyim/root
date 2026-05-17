from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    spec_data: dict
    calibration_compliant: bool
    validation_errors: List[str]

def validate_specs(state: LabEquipmentState):
    errors = []
    if 'calibration_cert' not in state['spec_data']:
        errors.append('Missing Calibration Certificate')
    return {'validation_errors': errors, 'calibration_compliant': len(errors) == 0}

def approval_node(state: LabEquipmentState):
    return {'validation_errors': ['Pending QA Review'] if state['calibration_compliant'] else ['Rejected']}

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
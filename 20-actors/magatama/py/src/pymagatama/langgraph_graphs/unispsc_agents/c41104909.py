from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabEquipmentState(TypedDict):
    spec_data: dict
    validation_status: str

def validate_specs(state: LabEquipmentState):
    required = ['material', 'pressure_rating']
    if all(k in state['spec_data'] for k in required):
        return {'validation_status': 'passed'}
    return {'validation_status': 'failed'}

def route_by_validation(state: LabEquipmentState):
    return 'process' if state['validation_status'] == 'passed' else END

graph = StateGraph(LabEquipmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END})
graph.compile()

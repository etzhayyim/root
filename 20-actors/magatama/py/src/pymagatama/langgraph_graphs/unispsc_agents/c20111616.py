from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ClampState(TypedDict):
    part_number: str
    material: str
    required_torque: float
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_material(state: ClampState) -> ClampState:
    if state['material'] in ['stainless_steel', 'carbon_steel']:
        return {'validation_logs': ['Material validated successfully.']}
    return {'validation_logs': ['Material verification failed.']}

def check_torque_compliance(state: ClampState) -> ClampState:
    if state['required_torque'] > 0:
        return {'validation_logs': ['Torque specification is valid.'], 'is_approved': True}
    return {'validation_logs': ['Torque specification missing or invalid.'], 'is_approved': False}

graph = StateGraph(ClampState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_torque', check_torque_compliance)
graph.add_edge('validate_material', 'check_torque')
graph.add_edge('check_torque', END)
graph.set_entry_point('validate_material')
graph = graph.compile()
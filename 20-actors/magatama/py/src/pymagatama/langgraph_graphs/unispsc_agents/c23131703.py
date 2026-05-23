from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_robot_specs(state: RobotProcurementState):
    errors = []
    if state['specifications'].get('payload', 0) <= 0:
        errors.append('Invalid payload capacity')
    if not state['specifications'].get('iso_cert'):
        errors.append('Missing ISO 10218 certification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_robot_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

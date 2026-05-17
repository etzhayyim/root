from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_robot_specs(state: RobotState):
    spec = state['spec']
    errors = []
    if spec.get('payload_capacity_kg', 0) <= 0:
        errors.append('Invalid payload capacity')
    if not spec.get('safety_certification_iso10218', False):
        errors.append('Missing mandatory ISO10218 certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_procurement(state: RobotState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(RobotState)
graph.add_node('validator', validate_robot_specs)
graph.set_entry_point('validator')
graph.add_conditional_edges('validator', route_procurement, {'compliant': END, 'reject': END})

graph = graph.compile()
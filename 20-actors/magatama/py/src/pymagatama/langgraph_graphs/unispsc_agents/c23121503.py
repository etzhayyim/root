from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: RobotProcurementState):
    errors = []
    if not state['specifications'].get('payload_capacity_kg'):
        errors.append('Missing payload capacity')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def routing_logic(state: RobotProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: RobotState):
    errors = []
    if state['spec_data'].get('payload', 0) <= 0:
        errors.append('Invalid payload')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: RobotState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()

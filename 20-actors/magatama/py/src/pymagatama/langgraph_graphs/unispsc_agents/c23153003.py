from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RobotState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: RobotState):
    errors = []
    if state['spec_data'].get('payload', 0) <= 0:
        errors.append('Invalid payload capacity')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_export_control(state: RobotState):
    # Simulate dual-use check logic
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
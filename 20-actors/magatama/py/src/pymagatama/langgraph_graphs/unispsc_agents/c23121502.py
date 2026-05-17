from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    spec_data: dict
    validation_checks: List[str]
    is_compliant: bool

def validate_specs(state: RobotState):
    checks = []
    if state['spec_data'].get('payload', 0) > 0:
        checks.append('Payload Check Passed')
    state['validation_checks'] = checks
    state['is_compliant'] = len(checks) > 0
    return state

def export_approval(state: RobotState):
    # Dual-use control check
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_approval)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()
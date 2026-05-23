from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    robot_id: str
    spec_requirements: dict
    validation_passed: bool
    log: List[str]

def validate_robot_specs(state: RobotState):
    # Simulate spec validation
    passed = state['spec_requirements'].get('payload') > 0
    return {'validation_passed': passed, 'log': [f'Validation for {state['robot_id']}: {passed}']}

def prepare_robot_integration(state: RobotState):
    if state['validation_passed']:
        return {'log': ['Integration setup initialized']}
    return {'log': ['Integration halted due to invalid specs']}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_robot_specs)
graph.add_node('integrate', prepare_robot_integration)
graph.add_edge('validate', 'integrate')
graph.add_edge('integrate', END)
graph.set_entry_point('validate')
graph = graph.compile()

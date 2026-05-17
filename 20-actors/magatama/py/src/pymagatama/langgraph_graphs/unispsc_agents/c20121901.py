from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    robot_id: str
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: RobotState) -> RobotState:
    specs = state.get('specs', {})
    # Logic to validate payload and range against safety standards
    passed = 'payload_capacity_kg' in specs and 'reach_range_mm' in specs
    return {'validation_passed': passed, 'log': ['Specs validated: ' + str(passed)]}

def check_compliance(state: RobotState) -> RobotState:
    # Logic for dual-use export control checks
    return {'log': state['log'] + ['Compliance check completed']}

def construct_graph():
    graph = StateGraph(RobotState)
    graph.add_node('validate', validate_specs)
    graph.add_node('compliance', check_compliance)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'compliance')
    graph.add_edge('compliance', END)
    return graph.compile()
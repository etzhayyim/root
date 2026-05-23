from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotComponentState(TypedDict):
    component_id: str
    spec_requirements: dict
    validation_log: List[str]
    approved: bool

def validate_specs(state: RobotComponentState) -> RobotComponentState:
    # Simulate CAD/Tolerance validation logic
    tolerance = state['spec_requirements'].get('precision_tolerance_mm', 1.0)
    if tolerance <= 0.05:
        state['validation_log'].append('High precision validation passed.')
        state['approved'] = True
    else:
        state['validation_log'].append('Tolerance out of range.')
        state['approved'] = False
    return state

def check_compliance(state: RobotComponentState) -> RobotComponentState:
    # Simulate dual-use export control check
    if state.get('approved'):
        state['validation_log'].append('Compliance review cleared.')
    return state

graph = StateGraph(RobotComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

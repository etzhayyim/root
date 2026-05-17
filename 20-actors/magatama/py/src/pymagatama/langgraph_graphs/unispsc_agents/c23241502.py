from typing import TypedDict
from langgraph.graph import StateGraph, END
class RobotState(TypedDict):
    payload: float
    safety_compliant: bool
    validation_passed: bool
def validate_specs(state: RobotState):
    state['validation_passed'] = state['payload'] > 0 and state['safety_compliant']
    return state
graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HardwareState(TypedDict):
    specification: str
    validation_passed: bool
    torque_requirements: float

def validate_specs(state: HardwareState):
    state['validation_passed'] = bool(state.get('specification') and state.get('torque_requirements', 0) > 0)
    return state

def check_compliance(state: HardwareState):
    print(f'Compliance check for spec: {state.get("specification")}')
    return 'end'

graph = StateGraph(HardwareState)
graph.add_node('validator', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validator')
graph.add_edge('validator', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_torque(state: ToolState):
    torque = state['specs'].get('torque_nm', 0)
    state['validation_passed'] = torque > 0
    return state

def check_compliance(state: ToolState):
    return 'compliant' if state['validation_passed'] else 'non_compliant'

graph = StateGraph(ToolState)
graph.add_node('validate', validate_torque)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
process = graph.compile()

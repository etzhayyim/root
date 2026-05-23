from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_id: str
    torque_setting: float
    requires_calibration: bool
    approved: bool

def validate_torque(state: ToolState):
    state['approved'] = state['torque_setting'] > 0
    return state

def check_compliance(state: ToolState):
    state['requires_calibration'] = True
    return state

graph = StateGraph(ToolState)
graph.add_node('validate', validate_torque)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()

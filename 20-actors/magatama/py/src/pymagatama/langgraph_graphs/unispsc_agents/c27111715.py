from typing import TypedDict
from langgraph.graph import StateGraph, END

class TorqueToolState(TypedDict):
    tool_id: str
    torque_range: float
    calibrated: bool
    approved: bool

def validate_calibration(state: TorqueToolState):
    state['approved'] = state.get('calibrated', False)
    return state

def check_torque_limits(state: TorqueToolState):
    if state['torque_range'] > 0:
        print('Range valid')
    return state

graph = StateGraph(TorqueToolState)
graph.add_node('validate', validate_calibration)
graph.add_node('limits', check_torque_limits)
graph.set_entry_point('validate')
graph.add_edge('validate', 'limits')
graph.add_edge('limits', END)
graph = graph.compile()

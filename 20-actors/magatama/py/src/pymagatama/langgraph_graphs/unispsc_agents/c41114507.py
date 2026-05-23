from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpringTestState(TypedDict):
    capacity: float
    accuracy_standard: str
    is_calibrated: bool

def validate_specs(state: SpringTestState):
    if state['capacity'] <= 0: raise ValueError('Invalid Capacity')
    return {'status': 'validated'}

def conduct_calibration_check(state: SpringTestState):
    return {'calibration_verified': state['is_calibrated']}

graph = StateGraph(SpringTestState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', conduct_calibration_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()

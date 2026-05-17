from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IronLungState(TypedDict):
    device_id: str
    pressure_bounds: float
    certification_verified: bool
    safety_check_passed: bool

def validate_pressure(state: IronLungState):
    state['safety_check_passed'] = state['pressure_bounds'] > 0
    return {'safety_check_passed': state['safety_check_passed']}

def approval_step(state: IronLungState):
    return {'certification_verified': True}

graph = StateGraph(IronLungState)
graph.add_node('validate_pressure', validate_pressure)
graph.add_node('approval_step', approval_step)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'approval_step')
graph.add_edge('approval_step', END)
app = graph.compile()
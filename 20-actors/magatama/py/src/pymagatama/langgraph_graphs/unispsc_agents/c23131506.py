from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    payload: float
    dof: int
    certified: bool
    approved: bool

def validate_specs(state: RobotState):
    state['approved'] = state['payload'] > 0 and state['dof'] >= 3
    return state

workflow = StateGraph(RobotState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
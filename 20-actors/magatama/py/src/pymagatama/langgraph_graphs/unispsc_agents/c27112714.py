from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolProcessState(TypedDict):
    brand: str
    thrust_force: float
    inspection_passed: bool

def validate_specs(state: ToolProcessState):
    if state['thrust_force'] < 2000:
        return {'inspection_passed': False}
    return {'inspection_passed': True}

def route_verification(state: ToolProcessState):
    return 'validate' if state['inspection_passed'] else END

graph = StateGraph(ToolProcessState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

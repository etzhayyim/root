from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    model_id: str
    payload: float
    compliance_checked: bool

def validate_specs(state: RobotState):
    state['compliance_checked'] = state['payload'] > 0
    return state

def check_dual_use(state: RobotState):
    # Simulate regulatory check
    return {'compliance_checked': True}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
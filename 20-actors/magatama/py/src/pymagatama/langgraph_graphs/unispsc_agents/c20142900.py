from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotPartState(TypedDict):
    part_id: str
    specs: dict
    approved: bool

def validate_specs(state: RobotPartState):
    # Simulate CAD/Tolerance validation logic
    is_valid = state['specs'].get('tolerance', 0) < 0.05
    return {'approved': is_valid}

def update_status(state: RobotPartState):
    return {'approved': state['approved']}

graph = StateGraph(RobotPartState)
graph.add_node('validate', validate_specs)
graph.add_node('status', update_status)
graph.add_edge('validate', 'status')
graph.add_edge('status', END)
graph.set_entry_point('validate')
graph = graph.compile()

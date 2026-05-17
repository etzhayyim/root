from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class RobotState(TypedDict):
    task_id: str
    payload_kg: float
    steps: List[str]
    status: str

def validate_payload(state: RobotState) -> RobotState:
    if state['payload_kg'] > 50.0:
        state['status'] = 'MANUAL_REVIEW_REQUIRED'
    else:
        state['status'] = 'VALIDATED'
    return state

def plan_path(state: RobotState) -> RobotState:
    state['steps'].append('calculate_kinematics')
    state['steps'].append('collision_check')
    return state

graph = StateGraph(RobotState)
graph.add_node('validator', validate_payload)
graph.add_node('planner', plan_path)
graph.set_entry_point('validator')
graph.add_edge('validator', 'planner')
graph.add_edge('planner', END)
app = graph.compile()
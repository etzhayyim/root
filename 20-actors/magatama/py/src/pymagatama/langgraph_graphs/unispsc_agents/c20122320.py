from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class RobotState(TypedDict):
    task_id: str
    arm_id: str
    payload: float
    status: str
    logs: Annotated[List[str], operator.add]

def validate_payload(state: RobotState):
    if state['payload'] > 50.0:
        return {'status': 'error', 'logs': ['Payload exceeds safety limit for this arm model']}
    return {'status': 'validated', 'logs': ['Payload within safe operational parameters']}

def execute_motion_plan(state: RobotState):
    if state['status'] == 'validated':
        return {'status': 'executing', 'logs': ['Motion trajectory generated and uploaded to controller']}
    return {'status': 'aborted', 'logs': ['Motion execution cancelled due to invalid state']}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_payload)
graph.add_node('execute', execute_motion_plan)
graph.set_entry_point('validate')
graph.add_edge('validate', 'execute')
graph.add_edge('execute', END)
graph = graph.compile()
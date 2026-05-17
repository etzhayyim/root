from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    task_id: str
    geometry: dict
    welding_params: dict
    is_validated: bool
    error_log: List[str]

def validate_geometry(state: RobotState) -> RobotState:
    # Logic to validate CAD/geometry against robot constraints
    if not state.get('geometry'):
        state['error_log'].append('Invalid geometry')
    state['is_validated'] = True
    return state

def plan_weld_path(state: RobotState) -> RobotState:
    # Generate optimized motion path
    state['welding_params'] = {'path_nodes': 50, 'speed': 250}
    return state

graph = StateGraph(RobotState)
graph.add_node('validate', validate_geometry)
graph.add_node('plan', plan_weld_path)
graph.add_edge('validate', 'plan')
graph.add_edge('plan', END)
graph.set_entry_point('validate')
robot_graph = graph.compile()
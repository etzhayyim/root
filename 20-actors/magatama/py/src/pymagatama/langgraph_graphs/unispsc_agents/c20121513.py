from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    payload: float
    precision: float
    workflow_steps: List[str]
    validation_status: str

def validate_specs(state: RobotState):
    status = 'PASS' if state['payload'] > 0 and state['precision'] < 0.1 else 'FAIL'
    return {'validation_status': status}

def plan_tasks(state: RobotState):
    return {'workflow_steps': ['Initialize', 'Calibrate', 'Run Cycle', 'Safety Check']}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_specs)
graph.add_node('plan', plan_tasks)
graph.add_edge('validate', 'plan')
graph.add_edge('plan', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()

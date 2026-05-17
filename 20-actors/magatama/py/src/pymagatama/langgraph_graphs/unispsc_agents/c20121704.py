from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class RobotState(TypedDict):
    task_id: str
    payload: Dict[str, Any]
    validation_log: List[str]
    approved: bool

def validate_specs(state: RobotState) -> RobotState:
    payload = state['payload']
    logs = state.get('validation_log', [])
    if payload.get('load_capacity_kg', 0) > 500:
        logs.append('Warning: High load capacity requires secondary structural verification.')
    state['validation_log'] = logs
    return state

def check_compliance(state: RobotState) -> RobotState:
    state['approved'] = True
    return state

builder = StateGraph(RobotState)
builder.add_node('validate', validate_specs)
builder.add_node('compliance', check_compliance)
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
builder.set_entry_point('validate')
graph = builder.compile()
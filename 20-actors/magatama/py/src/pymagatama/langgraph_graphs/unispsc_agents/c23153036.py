from typing import TypedDict
from langgraph.graph import StateGraph, END

class RobotPartState(TypedDict):
    part_id: str
    compliance_check: bool
    maintenance_window: bool

def validate_compliance(state: RobotPartState):
    state['compliance_check'] = state['part_id'].startswith('ROB')
    return state

def schedule_maintenance(state: RobotPartState):
    state['maintenance_window'] = True
    return state

graph = StateGraph(RobotPartState)
graph.add_node('validate', validate_compliance)
graph.add_node('schedule', schedule_maintenance)
graph.add_edge('validate', 'schedule')
graph.add_edge('schedule', END)
graph.set_entry_point('validate')
graph = graph.compile()

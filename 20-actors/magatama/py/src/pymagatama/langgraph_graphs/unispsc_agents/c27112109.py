from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    pull_force: float
    status: str

def validate_magnetic_force(state: ToolState):
    if state['pull_force'] <= 0:
        return {'status': 'INVALID_FORCE'}
    return {'status': 'VALIDATED'}

def route_inspection(state: ToolState):
    return 'END' if state['status'] == 'VALIDATED' else 'END'

graph = StateGraph(ToolState)
graph.add_node('validate', validate_magnetic_force)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()

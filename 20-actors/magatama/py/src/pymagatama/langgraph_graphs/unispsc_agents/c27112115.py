from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    jaw_capacity: float
    status: str

def validate_clamp_force(state: ToolState):
    print('Validating clamping specification...')
    state['status'] = 'verified' if state['jaw_capacity'] > 0 else 'failed'
    return state

def safety_check(state: ToolState):
    print('Performing mechanical integrity check...')
    return {'status': 'approved' if state['status'] == 'verified' else 'rejected'}

graph = StateGraph(ToolState)
graph.add_node('validate', validate_clamp_force)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
app = graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MountState(TypedDict):
    vesa_compliance: bool
    max_load: float
    inspection_status: str

def validate_specs(state: MountState):
    if state['vesa_compliance'] and state['max_load'] > 0:
        return {'inspection_status': 'PASSED'}
    return {'inspection_status': 'FAILED'}

def deploy_mount(state: MountState):
    print(f'Mount workflow finalized: {state["inspection_status"]}')
    return state

builder = StateGraph(MountState)
builder.add_node('validate', validate_specs)
builder.add_node('deploy', deploy_mount)
builder.set_entry_point('validate')
builder.add_edge('validate', 'deploy')
builder.add_edge('deploy', END)
graph = builder.compile()

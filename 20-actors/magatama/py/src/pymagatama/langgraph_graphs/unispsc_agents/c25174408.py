from typing import TypedDict
from langgraph.graph import StateGraph, END

class PowerPortState(TypedDict):
    part_id: str
    specs: dict
    validated: bool

def validate_specs(state: PowerPortState):
    required = ['Rated Voltage', 'Operating Temperature Range']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def safety_check(state: PowerPortState):
    if state.get('validated') and state['specs'].get('Rated Voltage', 0) > 0:
        return 'approve'
    return 'reject'

graph = StateGraph(PowerPortState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', safety_check, {'approve': END, 'reject': END})
from langgraph.graph import StateGraph, END
from typing import TypedDict
class MixerState(TypedDict):
    specs: dict
    approved: bool
def validate_specs(state: MixerState):
    required = ['Motor Power', 'Safety Certification']
    state['approved'] = all(k in state['specs'] for k in required)
    return state
def route_procurement(state: MixerState):
    return 'approve' if state['approved'] else 'reject'
graph = StateGraph(MixerState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
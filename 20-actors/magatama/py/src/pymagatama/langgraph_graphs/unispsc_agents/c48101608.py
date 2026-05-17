from typing import TypedDict
from langgraph.graph import StateGraph, END

class MixerState(TypedDict):
    spec_sheet: dict
    approved: bool

def validate_nsf(state: MixerState):
    state['approved'] = state['spec_sheet'].get('nsf_certified', False)
    return state

def validate_power(state: MixerState):
    if state['spec_sheet'].get('hp', 0) < 0.5: state['approved'] = False
    return state

graph = StateGraph(MixerState)
graph.add_node('nsf', validate_nsf)
graph.add_node('power', validate_power)
graph.set_entry_point('nsf')
graph.add_edge('nsf', 'power')
graph.add_edge('power', END)
graph = graph.compile()
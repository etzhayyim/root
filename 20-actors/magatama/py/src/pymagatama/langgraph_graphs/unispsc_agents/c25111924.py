from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadarSpecState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_rcs(state: RadarSpecState):
    state['validated'] = state['spec_data'].get('rcs', 0) >= 2.5
    return state

def check_compliance(state: RadarSpecState):
    if state['validated']:
        state['error_log'].append('Compliance OK')
    return state

graph = StateGraph(RadarSpecState)
graph.add_node('validate', validate_rcs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class OrthoState(TypedDict):
    spec_data: dict
    validated: bool

def validate_biocompatibility(state: OrthoState):
    iso_req = state['spec_data'].get('biocompatibility_iso_standard')
    state['validated'] = iso_req == 'ISO 10993'
    return state

def check_setting_time(state: OrthoState):
    time = state['spec_data'].get('setting_time_minutes', 0)
    if 2 <= time <= 10:
        state['validated'] = state['validated'] and True
    else:
        state['validated'] = False
    return state

graph = StateGraph(OrthoState)
graph.add_node('biocompatibility_check', validate_biocompatibility)
graph.add_node('time_check', check_setting_time)
graph.set_entry_point('biocompatibility_check')
graph.add_edge('biocompatibility_check', 'time_check')
graph.add_edge('time_check', END)
graph = graph.compile()

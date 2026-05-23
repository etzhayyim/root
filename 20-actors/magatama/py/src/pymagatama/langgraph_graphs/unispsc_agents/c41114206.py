from typing import TypedDict
from langgraph.graph import StateGraph, END

class HubState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_hub_specs(state: HubState):
    required = ['Interface Standards', 'Data Transmission Rate']
    all_present = all(k in state['specs'] for k in required)
    return {'validated': all_present, 'error': '' if all_present else 'Missing fields'}

def route_verification(state: HubState):
    return 'valid' if state['validated'] else END

graph = StateGraph(HubState)
graph.add_node('validation', validate_hub_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')

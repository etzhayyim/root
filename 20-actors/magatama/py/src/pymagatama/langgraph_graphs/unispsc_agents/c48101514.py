from typing import TypedDict
from langgraph.graph import StateGraph, END

class SteamState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_pressure(state: SteamState):
    pressure = state['specs'].get('pressure', 0)
    is_valid = 0 < pressure <= 1.0
    return {'validated': is_valid, 'error_log': [] if is_valid else ['High pressure limit exceeded']}

def route_by_validation(state: SteamState):
    return 'validate' if not state['validated'] else END

graph = StateGraph(SteamState)
graph.add_node('validate', validate_pressure)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
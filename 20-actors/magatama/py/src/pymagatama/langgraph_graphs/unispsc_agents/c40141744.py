from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrainBowlState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_pressure_specs(state: DrainBowlState):
    pressure = state['spec_data'].get('pressure_rating', 0)
    valid = pressure > 0
    return {'validated': valid, 'error_log': ['Invalid pressure' if not valid else 'OK']}

def route_by_spec(state: DrainBowlState):
    return 'process' if state['validated'] else END

graph = StateGraph(DrainBowlState)
graph.add_node('validate', validate_pressure_specs)
graph.add_node('process', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_spec)
graph.add_edge('process', END)
graph = graph.compile()

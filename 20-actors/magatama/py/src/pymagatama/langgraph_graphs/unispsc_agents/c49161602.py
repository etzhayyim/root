from typing import TypedDict
from langgraph.graph import StateGraph, END

class RacketState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: RacketState):
    required = ['material', 'tension', 'weight']
    all_present = all(key in state['spec_data'] for key in required)
    return {'validated': all_present}

def route_verification(state: RacketState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(RacketState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
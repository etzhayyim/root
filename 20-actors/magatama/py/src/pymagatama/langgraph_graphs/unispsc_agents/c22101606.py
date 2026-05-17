from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    specs: dict
    approved: bool

def validate_load_capacity(state: BearingState):
    load = state['specs'].get('dynamic_load_rating', 0)
    return {'approved': load > 0}

def verify_specs(state: BearingState):
    required = ['bearing_material', 'iso_precision_grade']
    return {'approved': all(k in state['specs'] for k in required)}

graph = StateGraph(BearingState)
graph.add_node('load_check', validate_load_capacity)
graph.add_node('spec_check', verify_specs)
graph.add_edge('load_check', 'spec_check')
graph.add_edge('spec_check', END)
graph.set_entry_point('load_check')
graph = graph.compile()
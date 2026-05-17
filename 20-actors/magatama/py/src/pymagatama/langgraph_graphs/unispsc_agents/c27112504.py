from typing import TypedDict
from langgraph.graph import StateGraph, END

class WedgeState(TypedDict):
    spec_data: dict
    validation_report: dict

def validate_wedge_specs(state: WedgeState):
    specs = state['spec_data']
    valid = 'material' in specs and 'dimensions' in specs
    return {'validation_report': {'status': 'pass' if valid else 'fail'}}

def check_load_rating(state: WedgeState):
    rating = state['spec_data'].get('load_rating', 0)
    return {'validation_report': {'load_certified': rating > 0}}

graph = StateGraph(WedgeState)
graph.add_node('validate', validate_wedge_specs)
graph.add_node('load_check', check_load_rating)
graph.set_entry_point('validate')
graph.add_edge('validate', 'load_check')
graph.add_edge('load_check', END)
graph = graph.compile()
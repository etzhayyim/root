from langgraph.graph import StateGraph, END
from typing import TypedDict
class DryerState(TypedDict):
    specs: dict
    approved: bool
def validate_tech_specs(state: DryerState):
    required = ['IP-rating', 'power-input']
    valid = all(k in state['specs'] for k in required)
    return {'approved': valid}
def workflow():
    graph = StateGraph(DryerState)
    graph.add_node('validate', validate_tech_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class MoldState(TypedDict):
    spec_data: dict
    validated: bool

def validate_thermal_specs(state: MoldState):
    temp = state['spec_data'].get('max_temp', 0)
    return {'validated': temp > 800}

def finalize_order(state: MoldState):
    return {'validated': True}

graph = StateGraph(MoldState)
graph.add_node('validate', validate_thermal_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShelterState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_durability(state: ShelterState):
    res = {'passed': state['spec_data'].get('wind_load', 0) > 100}
    return {'validation_results': [res]}

def check_compliance(state: ShelterState):
    approved = all(r.get('passed', False) for r in state['validation_results'])
    return {'is_approved': approved}

graph = StateGraph(ShelterState)
graph.add_node('validate', validate_durability)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
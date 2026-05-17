from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TankSpecState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_pressure(state: TankSpecState):
    errors = []
    if state['spec_data'].get('pressure_rating_mpa', 0) > 20:
        errors.append('High pressure threshold exceeded: requires manual safety review.')
    return {'validation_errors': errors}

def final_check(state: TankSpecState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(TankSpecState)
graph.add_node('validate', validate_pressure)
graph.add_node('final', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)

compiled_graph = graph.compile()
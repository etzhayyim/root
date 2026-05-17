from typing import TypedDict
from langgraph.graph import StateGraph, END

class TankSpecState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: TankSpecState):
    s = state['specs']
    errors = []
    if s.get('pressure', 0) < 0.5: errors.append('Pressure insufficient')
    return {'validated': len(errors) == 0, 'error_log': errors}

def finalize_order(state: TankSpecState):
    return {'status': 'READY_FOR_PROCUREMENT'}

graph = StateGraph(TankSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingSpecState(TypedDict):
    specs: dict
    validated: bool
    errors: List[str]

def validate_specs(state: LightingSpecState):
    errors = []
    if state['specs'].get('wattage', 0) <= 0:
        errors.append('Invalid wattage')
    return {'validated': len(errors) == 0, 'errors': errors}

graph = StateGraph(LightingSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
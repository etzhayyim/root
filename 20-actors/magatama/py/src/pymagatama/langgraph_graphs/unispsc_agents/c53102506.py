from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SweatbandState(TypedDict):
    material: str
    specs: dict
    is_compliant: bool

def validate_material(state: SweatbandState):
    compliant = state['material'] in ['Cotton', 'Polyester blend', 'Spandex']
    return {'is_compliant': compliant}

def finalize_order(state: SweatbandState):
    return {'specs': {**state['specs'], 'status': 'Approved' if state['is_compliant'] else 'Rejected'}}

graph = StateGraph(SweatbandState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()

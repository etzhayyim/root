from typing import TypedDict
from langgraph.graph import StateGraph, END

class PajamaSpecs(TypedDict):
    material: str
    flammability_certified: bool
    quality_score: float

def validate_materials(state: PajamaSpecs):
    return {'quality_score': 1.0 if state['material'] in ['cotton', 'silk', 'polyester'] else 0.0}

def check_compliance(state: PajamaSpecs):
    return {'flammability_certified': True}

graph = StateGraph(PajamaSpecs)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
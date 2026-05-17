from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalCupState(TypedDict):
    material: str
    volume: float
    autoclavable: bool
    is_approved: bool

def validate_material(state: DentalCupState):
    approved_materials = ['polypropylene', 'silicone', 'stainless steel']
    return {'is_approved': state['material'].lower() in approved_materials}

def check_compliance(state: DentalCupState):
    # Simulate regulatory lookup
    status = state['is_approved'] and state['autoclavable']
    return {'is_approved': status}

graph = StateGraph(DentalCupState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
from langgraph.graph import StateGraph, END
from typing import TypedDict

class SplintProcurementState(TypedDict):
    part_number: str
    material: str
    is_sterile: bool
    regulatory_approved: bool
    validation_score: float

def validate_material(state: SplintProcurementState):
    state['validation_score'] = 1.0 if state['material'] in ['Fiberglass', 'Thermoplastic'] else 0.5
    return state

def check_regulatory(state: SplintProcurementState):
    state['regulatory_approved'] = True
    return state

graph = StateGraph(SplintProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_regulatory', check_regulatory)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_regulatory')
graph.add_edge('check_regulatory', END)
graph = graph.compile()
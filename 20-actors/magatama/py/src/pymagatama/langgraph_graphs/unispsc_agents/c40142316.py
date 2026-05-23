from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PipeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_pressure_rating(state: PipeState):
    rating = state['spec_data'].get('pressure_rating', 0)
    if rating < 150:
        state['validation_errors'].append('Pressure rating below minimum threshold.')
    return state

def check_material_compliance(state: PipeState):
    material = state['spec_data'].get('material', '')
    if material not in ['Carbon Steel', 'Stainless Steel 316']:
        state['validation_errors'].append('Non-compliant material grade.')
    return state

graph = StateGraph(PipeState)
graph.add_node('validate_pressure', validate_pressure_rating)
graph.add_node('check_material', check_material_compliance)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'check_material')
graph.add_edge('check_material', END)
app = graph.compile()

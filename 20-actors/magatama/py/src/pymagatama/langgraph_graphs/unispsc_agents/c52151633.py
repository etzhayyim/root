from typing import TypedDict
from langgraph.graph import StateGraph, END

class GarnishingToolState(TypedDict):
    tool_type: str
    material: str
    is_food_safe: bool
    validation_notes: list

def validate_material(state: GarnishingToolState):
    state['is_food_safe'] = state['material'] in ['stainless_steel_304', 'food_grade_silicone']
    return state

def check_compliance(state: GarnishingToolState):
    if not state.get('is_food_safe'):
        state['validation_notes'].append('Material safety non-compliance')
    return state

graph = StateGraph(GarnishingToolState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    spec_compliance: bool
    tip_precision_mm: float
    material_type: str

def validate_specs(state: ToolState):
    state['spec_compliance'] = state['tip_precision_mm'] < 0.1
    return state

def check_material(state: ToolState):
    state['material_type'] = 'Anti-magnetic' if state['material_type'] == 'Stainless' else 'Standard'
    return state

graph = StateGraph(ToolState)
graph.add_node('validate', validate_specs)
graph.add_node('material', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'material')
graph.add_edge('material', END)
graph = graph.compile()
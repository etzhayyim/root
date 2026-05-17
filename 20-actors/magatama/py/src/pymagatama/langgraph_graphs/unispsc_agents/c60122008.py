from typing import TypedDict
from langgraph.graph import StateGraph, END

class CraftMaterialState(TypedDict):
    material: str
    quality_check: bool
    approved: bool

def validate_material(state: CraftMaterialState):
    # Simulate material validation logic for plastic lacing
    state['quality_check'] = 'plastic' in state['material'].lower() and 'non-toxic' in state.get('certs', [])
    return {'quality_check': state['quality_check']}

def final_approval(state: CraftMaterialState):
    state['approved'] = state['quality_check']
    return {'approved': state['approved']}

graph = StateGraph(CraftMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()
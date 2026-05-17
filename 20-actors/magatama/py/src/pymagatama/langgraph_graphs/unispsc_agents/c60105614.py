from typing import TypedDict
from langgraph.graph import StateGraph, END

class KitchenMaterialState(TypedDict):
    content: str
    compliance_check: bool
    approved: bool

def validate_content(state: KitchenMaterialState):
    # Simulated validation logic for safety materials
    state['compliance_check'] = 'HACCP' in state['content']
    return state

def review_material(state: KitchenMaterialState):
    state['approved'] = state['compliance_check']
    return state

graph = StateGraph(KitchenMaterialState)
graph.add_node('validate', validate_content)
graph.add_node('review', review_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'review')
graph.add_edge('review', END)
graph = graph.compile()
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ArtMaterialState(TypedDict):
    material_name: str
    sds_status: bool
    safety_rating: str
    is_approved: bool

def validate_sds(state: ArtMaterialState):
    state['sds_status'] = True
    return state

def check_toxicity(state: ArtMaterialState):
    state['is_approved'] = (state['safety_rating'] == 'AP')
    return state

graph = StateGraph(ArtMaterialState)
graph.add_node('validate_sds', validate_sds)
graph.add_node('check_toxicity', check_toxicity)
graph.add_edge('validate_sds', 'check_toxicity')
graph.add_edge('check_toxicity', END)
graph.set_entry_point('validate_sds')
graph = graph.compile()
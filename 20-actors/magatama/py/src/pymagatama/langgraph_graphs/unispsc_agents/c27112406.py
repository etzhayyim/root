from typing import TypedDict
from langgraph.graph import StateGraph, END

class TagGunState(TypedDict):
    model_id: str
    compliance_checked: bool
    safety_rating: str

def validate_tag_gun_model(state: TagGunState):
    state['compliance_checked'] = state['model_id'].startswith('TG-')
    return state

def check_safety(state: TagGunState):
    state['safety_rating'] = 'Pass' if state['compliance_checked'] else 'Fail'
    return state

graph = StateGraph(TagGunState)
graph.add_node('validate', validate_tag_gun_model)
graph.add_node('safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
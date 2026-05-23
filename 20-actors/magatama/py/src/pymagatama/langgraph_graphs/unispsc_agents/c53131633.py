from typing import TypedDict
from langgraph.graph import StateGraph, END

class BarretteState(TypedDict):
    specs: dict
    approved: bool

def validate_material(state: BarretteState):
    state['approved'] = 'lead_free' in state['specs']
    return state

def check_durability(state: BarretteState):
    state['approved'] = state['approved'] and state['specs'].get('clasp_cycle', 0) > 1000
    return state

graph = StateGraph(BarretteState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_durability', check_durability)
graph.add_edge('validate_material', 'check_durability')
graph.add_edge('check_durability', END)
graph.set_entry_point('validate_material')
graph = graph.compile()

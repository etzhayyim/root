from typing import TypedDict
from langgraph.graph import StateGraph, END

class ManholeState(TypedDict):
    load_rating: str
    material: str
    is_compliant: bool

def validate_specs(state: ManholeState):
    state['is_compliant'] = state['load_rating'] in ['D400', 'E600'] and state['material'] == 'Ductile Iron'
    return state

graph = StateGraph(ManholeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

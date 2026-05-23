from typing import TypedDict
from langgraph.graph import StateGraph, END
class PipeState(TypedDict):
    material: str
    quality_score: float
    compliant: bool

def validate_material(state: PipeState):
    state['compliant'] = state['material'] in ['briar', 'meerschaum', 'hardwood']
    return state

def calculate_score(state: PipeState):
    state['quality_score'] = 1.0 if state['compliant'] else 0.0
    return state

graph = StateGraph(PipeState)
graph.add_node('validate', validate_material)
graph.add_node('score', calculate_score)
graph.add_edge('validate', 'score')
graph.add_edge('score', END)
graph.set_entry_point('validate')
graph = graph.compile()

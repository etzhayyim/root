from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AbrasiveSpecs(TypedDict):
    grit: int
    material: str
    is_waterproof: bool
    validation_status: str

class GraphState(TypedDict):
    specs: AbrasiveSpecs
    errors: List[str]

def validate_grit(state: GraphState):
    if state['specs']['grit'] < 40 or state['specs']['grit'] > 3000:
        return {'errors': ['Grit size outside standard industrial range.']}
    return {'errors': []}

def process_procurement(state: GraphState):
    status = 'Validated' if not state['errors'] else 'Rejected'
    return {'specs': {**state['specs'], 'validation_status': status}}

graph = StateGraph(GraphState)
graph.add_node('validate', validate_grit)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
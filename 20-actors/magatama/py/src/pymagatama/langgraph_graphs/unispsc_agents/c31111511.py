from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PreciousMetalState(TypedDict):
    purity_level: float
    weight_kg: float
    dimensions_mm: List[float]
    verification_passed: bool

def validate_metal(state: PreciousMetalState):
    state['verification_passed'] = state['purity_level'] >= 99.9
    return state

def process_procurement(state: PreciousMetalState):
    print(f'Processing procurement for {state['weight_kg']}kg of precious metal.')
    return state

graph = StateGraph(PreciousMetalState)
graph.add_node('validate', validate_metal)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()

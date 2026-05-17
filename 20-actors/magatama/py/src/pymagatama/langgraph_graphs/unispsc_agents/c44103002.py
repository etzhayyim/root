from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FuserOilState(TypedDict):
    part_number: str
    viscosity: float
    compatibility: List[str]
    approved: bool

def validate_specs(state: FuserOilState):
    state['approved'] = state['viscosity'] > 0 and len(state['compatibility']) > 0
    return state

def compile_graph():
    graph = StateGraph(FuserOilState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = compile_graph()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForensicState(TypedDict):
    chemical_name: str
    purity_level: float
    has_sds: bool
    is_approved: bool

def validate_chemistry(state: ForensicState):
    if state['purity_level'] >= 0.99 and state['has_sds']:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(ForensicState)
graph.add_node('validate', validate_chemistry)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()
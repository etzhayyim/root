from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoinTrayState(TypedDict):
    material: str
    capacity: int
    is_stackable: bool

def validate_specs(state: CoinTrayState):
    if state['capacity'] <= 0:
        raise ValueError('Invalid capacity')
    return {'status': 'validated'}

graph = StateGraph(CoinTrayState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

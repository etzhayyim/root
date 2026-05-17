from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeSpecState(TypedDict):
    material: str
    pressure_rating: float
    is_compliant: bool

def validate_specs(state: PipeSpecState):
    state['is_compliant'] = (state['pressure_rating'] > 0 and len(state['material']) > 0)
    return state

def check_certification(state: PipeSpecState):
    print(f'Checking compliance for {state['material']}')
    return state

graph = StateGraph(PipeSpecState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
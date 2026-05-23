from typing import TypedDict
from langgraph.graph import StateGraph, END

class CornerGuardState(TypedDict):
    material: str
    shock_rating: int
    is_compliant: bool

def validate_spec(state: CornerGuardState):
    state['is_compliant'] = state['shock_rating'] >= 5
    return state

def assembly_instruction(state: CornerGuardState):
    print(f'Processing procurement for material: {state['material']}')
    return state

graph = StateGraph(CornerGuardState)
graph.add_node('validate', validate_spec)
graph.add_node('assemble', assembly_instruction)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph = graph.compile()

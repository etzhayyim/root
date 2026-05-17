from typing import TypedDict
from langgraph.graph import StateGraph, END

class RubberMoldingState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_molding(state: RubberMoldingState):
    hardness = state['specs'].get('shore_a', 0)
    state['validation_passed'] = 50 <= hardness <= 90
    return 'validate_molding'

graph = StateGraph(RubberMoldingState)
graph.add_node('validate', validate_molding)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
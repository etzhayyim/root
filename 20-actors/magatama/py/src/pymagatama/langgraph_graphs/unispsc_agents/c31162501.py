from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShelfBracketState(TypedDict):
    bracket_type: str
    material: str
    load_capacity: float
    validation_passed: bool

def validate_specs(state: ShelfBracketState):
    if state['load_capacity'] > 0 and state['material'] in ['Steel', 'Aluminum', 'Plastic']:
        return {'validation_passed': True}
    return {'validation_passed': False}

def route_by_validation(state: ShelfBracketState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(ShelfBracketState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'validation_passed': True})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
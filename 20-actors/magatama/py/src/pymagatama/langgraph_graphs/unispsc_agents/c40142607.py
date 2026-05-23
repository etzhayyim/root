from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubeCapState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_pressure_rating(state: TubeCapState):
    rating = state['spec_data'].get('pressure_rating', 0)
    return {'validation_passed': rating > 0}

def final_check(state: TubeCapState):
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(TubeCapState)
graph.add_node('validate', validate_pressure_rating)
graph.add_node('final', final_check)
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph.set_entry_point('validate')
graph = graph.compile()

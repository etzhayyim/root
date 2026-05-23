from typing import TypedDict
from langgraph.graph import StateGraph, END

class TillerState(TypedDict):
    model_number: str
    validation_status: bool
    safety_check_passed: bool

def validate_tiller(state: TillerState):
    if state['model_number'].startswith('T-'):
        return {'validation_status': True}
    return {'validation_status': False}

def safety_check(state: TillerState):
    return {'safety_check_passed': True}

graph = StateGraph(TillerState)
graph.add_node('validate', validate_tiller)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()

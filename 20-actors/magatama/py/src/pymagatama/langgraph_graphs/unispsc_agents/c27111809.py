from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class BevelState(TypedDict):
    material: str
    angle: float
    qa_passed: bool

def validate_specs(state: BevelState):
    state['qa_passed'] = state['angle'] > 0 and state['material'] != 'unknown'
    return state

def route_verification(state: BevelState):
    return 'validate' if not state.get('qa_passed') else END

graph = StateGraph(BevelState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TypingAidState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_ergonomics(state: TypingAidState):
    # Simulate check for ergonomic standards
    passed = state['spec_data'].get('ergonomic_rating', 0) >= 4
    return {'validation_passed': passed, 'errors': [] if passed else ['Ergonomic rating low']}

def finalize_procurement(state: TypingAidState):
    return state

graph = StateGraph(TypingAidState)
graph.add_node('validate', validate_ergonomics)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
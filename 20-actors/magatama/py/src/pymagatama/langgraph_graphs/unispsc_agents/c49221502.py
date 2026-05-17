from typing import TypedDict
from langgraph.graph import StateGraph, END

class SportGoalState(TypedDict):
    dimensions: dict
    safety_rating: str
    is_compliant: bool

def validate_specs(state: SportGoalState):
    # Business logic for sport goal specification check
    required_fields = ['height', 'width', 'depth']
    state['is_compliant'] = all(k in state['dimensions'] for k in required_fields)
    return state

workflow = StateGraph(SportGoalState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
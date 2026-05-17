from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    nutrient_score: float
    safety_check: bool
    approved: bool

def validate_nutrients(state: FeedState) -> FeedState:
    state['safety_check'] = state['nutrient_score'] > 0.8
    return state

def approve_procurement(state: FeedState) -> FeedState:
    state['approved'] = state['safety_check']
    return state

graph = StateGraph(FeedState)
graph.add_node('validate', validate_nutrients)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
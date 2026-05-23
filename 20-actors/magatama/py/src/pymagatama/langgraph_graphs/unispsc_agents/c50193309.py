from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    commodity: str
    quality_score: float
    compliant: bool

def validate_food_safety(state: ProcessingState):
    state['compliant'] = state['quality_score'] >= 0.8
    return state

def check_shelf_life(state: ProcessingState):
    print('Verifying expiration dates and storage temperatures.')
    return state

graph = StateGraph(ProcessingState)
graph.add_node('safety_check', validate_food_safety)
graph.add_node('shelf_life_check', check_shelf_life)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'shelf_life_check')
graph.add_edge('shelf_life_check', END)
app = graph.compile()

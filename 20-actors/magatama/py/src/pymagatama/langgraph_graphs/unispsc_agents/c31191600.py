from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbrasiveState(TypedDict):
    rpm_rating: int
    max_safe_rpm: int
    validated: bool

def validate_rotation_speed(state: AbrasiveState):
    state['validated'] = state['rpm_rating'] <= state['max_safe_rpm']
    return state

graph = StateGraph(AbrasiveState)
graph.add_node('safety_check', validate_rotation_speed)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()

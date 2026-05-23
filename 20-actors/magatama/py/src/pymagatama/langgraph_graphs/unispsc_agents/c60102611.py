from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LogicGameState(TypedDict):
    game_title: str
    age_group: str
    safety_certs: List[str]
    approved: bool

def validate_safety(state: LogicGameState):
    required = ['ST_Mark', 'CE']
    state['approved'] = all(cert in state['safety_certs'] for cert in required)
    return state

def route_by_approval(state: LogicGameState):
    return "approved" if state['approved'] else "rejected"

graph = StateGraph(LogicGameState)
graph.add_node("safety_check", validate_safety)
graph.add_edge("safety_check", END)
graph.set_entry_point("safety_check")
graph = graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CashHandlingState(TypedDict):
    item_name: str
    security_level: int
    is_compliant: bool

def validate_equipment(state: CashHandlingState):
    # Business logic for verifying cash handling hardware compliance
    state['is_compliant'] = state['security_level'] >= 3
    return state

def route_verification(state: CashHandlingState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(CashHandlingState)
graph.add_node('validate', validate_equipment)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()

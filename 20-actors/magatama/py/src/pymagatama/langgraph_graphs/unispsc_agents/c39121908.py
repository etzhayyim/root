from typing import TypedDict
from langgraph.graph import StateGraph, END

class LockoutState(TypedDict):
    part_number: str
    compliance_check: bool
    safety_rating: str

def validate_safety_rating(state: LockoutState):
    valid = state['safety_rating'] in ['OSHA', 'ANSI', 'ISO']
    return {'compliance_check': valid}

def approval_step(state: LockoutState):
    print(f'Processing lockout device: {state["part_number"]}')
    return {'compliance_check': True}

graph = StateGraph(LockoutState)
graph.add_node('validate', validate_safety_rating)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
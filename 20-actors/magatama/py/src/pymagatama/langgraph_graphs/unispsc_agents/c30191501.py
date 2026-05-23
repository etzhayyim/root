from typing import TypedDict
from langgraph.graph import StateGraph, END

class LadderSpecState(TypedDict):
    load_capacity: float
    has_certification: bool
    passed_safety_check: bool

def validate_load(state: LadderSpecState):
    state['passed_safety_check'] = state['load_capacity'] >= 150
    return state

def check_cert(state: LadderSpecState):
    return {'passed_safety_check': state['has_certification']}

graph = StateGraph(LadderSpecState)
graph.add_node('validate_load', validate_load)
graph.add_node('check_cert', check_cert)
graph.set_entry_point('validate_load')
graph.add_edge('validate_load', 'check_cert')
graph.add_edge('check_cert', END)
graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class JuiceState(TypedDict):
    raw_data: dict
    validated: bool
    error_log: list

def validate_brix(state: JuiceState):
    brix = state['raw_data'].get('brix')
    is_valid = 10 <= brix <= 15
    return {'validated': is_valid, 'error_log': [] if is_valid else ['Invalid Brix level']}

def audit_safety(state: JuiceState):
    print('Checking pasteurization logs...')
    return {'validated': state['validated'] and True}

graph = StateGraph(JuiceState)
graph.add_node('brix_check', validate_brix)
graph.add_node('safety_audit', audit_safety)
graph.add_edge('brix_check', 'safety_audit')
graph.add_edge('safety_audit', END)
graph.set_entry_point('brix_check')
grapht = graph.compile()

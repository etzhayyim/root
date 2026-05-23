from typing import TypedDict
from langgraph.graph import StateGraph, END

class HepatitisAState(TypedDict):
    batch_id: str
    temp_log: float
    compliance_audit: bool

def validate_cold_chain(state: HepatitisAState):
    temp = state['temp_log']
    return {'compliance_audit': 2.0 <= temp <= 8.0}

def final_approval(state: HepatitisAState):
    return 'APPROVED' if state['compliance_audit'] else 'REJECTED'

graph = StateGraph(HepatitisAState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('approval', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class DairyState(TypedDict):
    temp_log: list[float]
    is_safe: bool
    compliance_docs: list[str]

def validate_cold_chain(state: DairyState):
    if all(temp <= 4.0 for temp in state['temp_log']):
        return {'is_safe': True}
    return {'is_safe': False}

def check_certification(state: DairyState):
    return {'is_safe': 'HACCP' in state['compliance_docs']}

graph = StateGraph(DairyState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('check_certification', check_certification)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'check_certification')
graph.add_edge('check_certification', END)
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class SMSCState(TypedDict):
    throughput_requirement: int
    protocol: str
    is_compliant: bool

def validate_load(state: SMSCState):
    state['is_compliant'] = state['throughput_requirement'] > 0
    return state

workflow = StateGraph(SMSCState)
workflow.add_node('load_check', validate_load)
workflow.set_entry_point('load_check')
workflow.add_edge('load_check', END)
graph = workflow.compile()
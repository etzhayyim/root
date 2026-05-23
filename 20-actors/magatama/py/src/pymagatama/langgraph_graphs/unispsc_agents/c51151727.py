from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    quality_docs: list
    is_approved: bool

def validate_gmp(state: ProcurementState):
    state['is_approved'] = 'gmp_cert' in state['quality_docs']
    return state

def check_temp_log(state: ProcurementState):
    print('Verifying temperature compliance for Norepinephrine')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('check_temp', check_temp_log)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'check_temp')
graph.add_edge('check_temp', END)
compile = graph.compile()

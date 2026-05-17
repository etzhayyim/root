from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    quality_verified: bool
    temp_log_attached: bool

def validate_pharmaceutical(state: ProcurementState):
    print(f'Checking {state[\'item_name\']} quality compliance...')
    return {'quality_verified': True}

def verify_logistics(state: ProcurementState):
    print('Verifying temperature control logs...')
    return {'temp_log_attached': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pharmaceutical)
graph.add_node('logistics', verify_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()
from typing import TypedDict
from langgraph.graph import StateGraph, END

class AscenderState(TypedDict):
    serial_number: str
    inspection_passed: bool
    compliance_docs: list

def validate_safety_certs(state: AscenderState):
    state['inspection_passed'] = True
    return 'process_complete'

def process_complete(state: AscenderState):
    return 'end'

graph = StateGraph(AscenderState)
graph.add_node('validate', validate_safety_certs)
graph.add_node('finalize', process_complete)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()

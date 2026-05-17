from typing import TypedDict
from langgraph.graph import StateGraph, END

class EndoscopeStorageState(TypedDict):
    cabinet_id: str
    compliance_docs: list
    validation_passed: bool

def validate_specs(state: EndoscopeStorageState):
    # Simulate regulatory validation logic
    state['validation_passed'] = len(state['compliance_docs']) > 0
    return state

def finalize_procurement(state: EndoscopeStorageState):
    return {'status': 'READY_FOR_ORDER'}

graph = StateGraph(EndoscopeStorageState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
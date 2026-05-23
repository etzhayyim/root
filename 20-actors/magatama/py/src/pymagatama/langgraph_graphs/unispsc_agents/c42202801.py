from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LithoState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    validation_passed: bool
    maintenance_cycle: int

def validate_specs(state: LithoState):
    state['validation_passed'] = 'ISO-13485' in state['compliance_docs']
    return state

def check_maintenance(state: LithoState):
    if state['maintenance_cycle'] > 12:
        state['validation_passed'] = False
    return state

graph = StateGraph(LithoState)
graph.add_node('validate', validate_specs)
graph.add_node('maintenance', check_maintenance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'maintenance')
graph.add_edge('maintenance', END)
graph = graph.compile()

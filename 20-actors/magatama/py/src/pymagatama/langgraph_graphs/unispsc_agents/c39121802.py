from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    part_number: str
    spec_compliance: bool
    inspection_status: str

def validate_specs(state: AuditState):
    state['spec_compliance'] = len(state['part_number']) > 5
    return {'spec_compliance': state['spec_compliance']}

def update_status(state: AuditState):
    state['inspection_status'] = 'VERIFIED' if state['spec_compliance'] else 'FAILED'
    return {'inspection_status': state['inspection_status']}

graph = StateGraph(AuditState)
graph.add_node('validate', validate_specs)
graph.add_node('mark', update_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'mark')
graph.add_edge('mark', END)
graph = graph.compile()
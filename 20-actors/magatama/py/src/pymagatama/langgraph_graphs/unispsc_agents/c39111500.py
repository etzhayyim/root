from typing import TypedDict
from langgraph.graph import StateGraph, END

class LightingSpecState(TypedDict):
    lumens: float
    ip_rating: str
    compliance_report: bool

def validate_specs(state: LightingSpecState):
    print('Validating lighting technical specs: lumination and IP rating...')
    return {'compliance_report': state['lumens'] > 0 and 'IP' in state['ip_rating']}

def approval_check(state: LightingSpecState):
    return 'approved' if state['compliance_report'] else 'rejected'

graph = StateGraph(LightingSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

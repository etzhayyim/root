from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MagnesiumState(TypedDict):
    purity: float
    inspection_result: str
    compliance_report: str

def validate_material(state: MagnesiumState):
    if state['purity'] >= 99.9:
        return {'inspection_result': 'PASS'}
    return {'inspection_result': 'FAIL'}

def check_compliance(state: MagnesiumState):
    return {'compliance_report': 'Verified against ASTM-B92'}

graph = StateGraph(MagnesiumState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LeatherState(TypedDict):
    material_type: str
    quality_grade: str
    compliance_docs: List[str]
    validation_result: bool

def validate_material(state: LeatherState):
    state['validation_result'] = 'leather_grade' in state and 'chemical_safety_compliance' in state
    return state

def check_compliance(state: LeatherState):
    state['compliance_docs'].append('REACH_Compliance')
    return state

graph = StateGraph(LeatherState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
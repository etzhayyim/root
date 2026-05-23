from langgraph.graph import StateGraph, END
from typing import TypedDict

class MedicalState(TypedDict):
    part_number: str
    compliance_docs: list
    is_sterile: bool
    approved: bool

def validate_compliance(state: MedicalState):
    state['approved'] = all([len(state['compliance_docs']) > 0, state['is_sterile']])
    return state

graph = StateGraph(MedicalState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

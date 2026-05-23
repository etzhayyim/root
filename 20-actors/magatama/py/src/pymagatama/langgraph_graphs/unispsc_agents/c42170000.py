from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MedicalSupplyState(TypedDict):
    items: List[str]
    validated: bool
    compliance_docs: List[str]

def validate_medical_standards(state: MedicalSupplyState):
    state['validated'] = all(doc.startswith('ISO') for doc in state['compliance_docs'])
    return state

def route_verification(state: MedicalSupplyState):
    return 'process' if state['validated'] else END

graph = StateGraph(MedicalSupplyState)
graph.add_node('validate', validate_medical_standards)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentureKitState(TypedDict):
    kit_id: str
    compliance_docs: list
    is_approved: bool

def validate_medical_compliance(state: DentureKitState):
    required_docs = {'ISO_13485', 'Biocompatibility_Report'}
    state['is_approved'] = required_docs.issubset(set(state['compliance_docs']))
    return state

def assembly_workflow(state: DentureKitState):
    print(f'Processing clinical validation for kit: {state['kit_id']}')
    return {'is_approved': True}

graph = StateGraph(DentureKitState)
graph.add_node('validate', validate_medical_compliance)
graph.add_node('assemble', assembly_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph = graph.compile()
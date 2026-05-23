from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MailMachineState(TypedDict):
    model_number: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: MailMachineState):
    required = ['license', 'calibration_cert']
    state['is_approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

def route_verification(state: MailMachineState):
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(MailMachineState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()

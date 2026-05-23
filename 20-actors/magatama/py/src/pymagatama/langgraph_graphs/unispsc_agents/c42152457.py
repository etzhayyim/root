from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalKitState(TypedDict):
    kit_id: str
    is_sterile: bool
    compliance_docs: list
    status: str

def validate_certification(state: DentalKitState):
    if 'ISO_13485' in state['compliance_docs']:
        return {'status': 'CERTIFIED'}
    return {'status': 'REJECTED'}

def check_sterility(state: DentalKitState):
    return {'is_sterile': True}

graph = StateGraph(DentalKitState)
graph.add_node('validate', validate_certification)
graph.add_node('sterility', check_sterility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterility')
graph.add_edge('sterility', END)
app = graph.compile()

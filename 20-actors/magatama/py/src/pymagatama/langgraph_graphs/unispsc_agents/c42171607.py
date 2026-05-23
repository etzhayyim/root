from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EMSState(TypedDict):
    collar_id: str
    compliance_docs: List[str]
    is_validated: bool

def validate_compliance(state: EMSState):
    # Simulate regulatory validation logic
    valid = all(doc in ['ISO13485', 'FDA_Clearance'] for doc in state['compliance_docs'])
    print(f'Validating collar {state['collar_id']}...')
    return {'is_validated': valid}

def routing_logic(state: EMSState):
    return 'valid' if state['is_validated'] else 'reject'

graph = StateGraph(EMSState)
graph.add_node('validate', validate_compliance)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToxicologyState(TypedDict):
    test_kit_id: str
    batch_number: str
    compliance_docs: List[str]
    validation_status: str

def validate_compliance(state: ToxicologyState):
    if all(doc in state['compliance_docs'] for doc in ['SDS', 'CoA']):
        return {'validation_status': 'CLEARED'}
    return {'validation_status': 'PENDING_REVIEW'}

def perform_logistics_check(state: ToxicologyState):
    print(f'Checking storage requirements for batch {state['batch_number']}')
    return {'validation_status': 'READY_FOR_SHIPMENT'}

graph = StateGraph(ToxicologyState)
graph.add_node('compliance', validate_compliance)
graph.add_node('logistics', perform_logistics_check)
graph.add_edge('compliance', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('compliance')
compiled_graph = graph.compile()
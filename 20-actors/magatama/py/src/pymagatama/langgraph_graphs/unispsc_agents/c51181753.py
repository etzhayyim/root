from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    commodity_code: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: ProcurementState):
    required = ['GMP_CERT', 'COA']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'is_approved': all_present}

def process_procurement(state: ProcurementState):
    print(f'Processing regulated shipment for {state.get('commodity_code')}')
    return {'is_approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
app = graph.compile()
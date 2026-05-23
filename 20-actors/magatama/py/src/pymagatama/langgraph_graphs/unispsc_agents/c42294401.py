from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HarvestSystemState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    validation_status: bool

def check_compliance(state: HarvestSystemState):
    required = ['ISO_13485', 'FDA_510k']
    return {'validation_status': all(doc in state['compliance_docs'] for doc in required)}

def finalize_procurement(state: HarvestSystemState):
    print(f'Finalizing procurement for {state.device_id}')

graph = StateGraph(HarvestSystemState)
graph.add_node('check_compliance', check_compliance)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('check_compliance', 'finalize')
graph.set_entry_point('check_compliance')
graph.add_edge('finalize', END)

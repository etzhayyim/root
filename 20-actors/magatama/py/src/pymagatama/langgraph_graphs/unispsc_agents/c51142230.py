from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    batch_id: str
    compliance_cleared: bool
    purity_validated: bool

def validate_compliance(state: DrugProcurementState):
    print(f'Checking compliance for batch: {state["batch_id"]}')
    return {'compliance_cleared': True}

def validate_purity(state: DrugProcurementState):
    print('Running HPLC purity validation...')
    return {'purity_validated': True}

graph = StateGraph(DrugProcurementState)
graph.add_node('compliance', validate_compliance)
graph.add_node('purity', validate_purity)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'purity')
graph.add_edge('purity', END)
graph = graph.compile()

from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    batch_id: str
    purity_level: float
    storage_temp: float
    is_compliant: bool

def validate_batch(state: ProcurementState):
    # Business logic for pharma grade verification
    compliant = state['purity_level'] >= 99.0 and state['storage_temp'] <= 25.0
    return {'is_compliant': compliant}

def record_compliance(state: ProcurementState):
    print(f'Batch {state['batch_id']} compliance status: {state['is_compliant']}')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_batch)
graph.add_node('record', record_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'record')
graph.add_edge('record', END)
graph = graph.compile()

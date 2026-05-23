from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    regulatory_clearance: bool
    batch_records: List[str]

def validate_compliance(state: ProcurementState):
    # Simulate regulatory check for controlled substances
    state['regulatory_clearance'] = True
    return state

def log_batch(state: ProcurementState):
    state['batch_records'].append('Verified Controlled Chain of Custody')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('log', log_batch)
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()

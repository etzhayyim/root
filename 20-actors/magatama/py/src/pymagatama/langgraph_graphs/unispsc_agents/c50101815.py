from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity: str
    quality_docs: List[str]
    is_cleared: bool

def validate_perishable_docs(state: ProcurementState):
    required = ['Origin Country', 'Phytosanitary Certificate']
    all_present = all(doc in state['quality_docs'] for doc in required)
    return {'is_cleared': all_present}

def route_by_clearance(state: ProcurementState):
    return 'pass' if state['is_cleared'] else 'fail'

graph = StateGraph(ProcurementState)
graph.add_node('validation', validate_perishable_docs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
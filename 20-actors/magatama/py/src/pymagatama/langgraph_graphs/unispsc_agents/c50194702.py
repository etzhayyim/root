from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcessingState(TypedDict):
    quality_score: float
    status: str

def validate_freshness(state: ProcessingState):
    # Simple logic for perishable quality check
    if state['quality_score'] < 0.8:
        return {'status': 'rejected'}
    return {'status': 'approved'}

graph = StateGraph(ProcessingState)
graph.add_node('qc_check', validate_freshness)
graph.set_entry_point('qc_check')
graph.add_edge('qc_check', END)
graph = graph.compile()
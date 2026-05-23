from typing import TypedDict
from langgraph.graph import StateGraph, END

class GelatinState(TypedDict):
    quality_cert: bool
    bloom_strength: float
    status: str

def validate_quality(state: GelatinState):
    status = 'approved' if state['quality_cert'] and state['bloom_strength'] >= 200 else 'rejected'
    return {'status': status}

workflow = StateGraph(GelatinState)
workflow.add_node('validation', validate_quality)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()

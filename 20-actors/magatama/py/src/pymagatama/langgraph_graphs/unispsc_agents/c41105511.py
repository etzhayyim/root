from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExtractionState(TypedDict):
    kit_id: str
    purity_check: bool
    yield_quality: float
    status: str

def validate_kits(state: ExtractionState):
    if state['purity_check'] and state['yield_quality'] > 0.95:
        return {'status': 'COMPLIANT'}
    return {'status': 'REJECTED'}

graph = StateGraph(ExtractionState)
graph.add_node('validate', validate_kits)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
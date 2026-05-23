from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class BioComponentState(TypedDict):
    component_id: str
    purity_check: bool
    temp_log: List[float]
    status: str

def validate_purity(state: BioComponentState):
    # Simulate CAD/Bio purity validation
    purity_ok = True
    return {'purity_check': purity_ok, 'status': 'validated'}

def check_cold_chain(state: BioComponentState):
    # Check for excursions
    excursion = any(t > 8.0 for t in state['temp_log'])
    return {'status': 'rejected' if excursion else 'cleared'}

graph = StateGraph(BioComponentState)
graph.add_node('validate', validate_purity)
graph.add_node('cold_chain', check_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', 'cold_chain')
graph.add_edge('cold_chain', END)
compile_graph = graph.compile()

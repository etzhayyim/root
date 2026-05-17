from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class CommodityState(TypedDict):
    batch_id: str
    purity_level: float
    inspection_results: Annotated[list[str], operator.add]
    is_approved: bool

def validate_purity(state: CommodityState) -> CommodityState:
    if state['purity_level'] >= 0.99:
        state['inspection_results'].append('Purity check passed')
        state['is_approved'] = True
    else:
        state['inspection_results'].append('Purity check failed')
        state['is_approved'] = False
    return state

def finalize_ingest(state: CommodityState) -> CommodityState:
    if state['is_approved']:
        state['inspection_results'].append('Ingestion completed')
    return state

graph = StateGraph(CommodityState)
graph.add_node('validate', validate_purity)
graph.add_node('finalize', finalize_ingest)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
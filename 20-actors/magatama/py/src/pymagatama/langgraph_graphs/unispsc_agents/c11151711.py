from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FlotationState(TypedDict):
    commodity_code: str
    reagent_purity: float
    test_results: List[str]
    approved: bool

def validate_purity(state: FlotationState):
    if state['reagent_purity'] >= 95.0:
        return {'approved': True, 'test_results': state['test_results'] + ['Purity pass']}
    return {'approved': False, 'test_results': state['test_results'] + ['Purity fail']}

def process_batch(state: FlotationState):
    return {'test_results': state['test_results'] + ['Batch processed']}

graph = StateGraph(FlotationState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

compiled_graph = graph.compile()

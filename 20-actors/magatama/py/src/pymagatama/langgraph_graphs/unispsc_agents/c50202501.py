from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ConcentrateState(TypedDict):
    batch_id: str
    brix_level: float
    is_compliant: bool
    test_results: List[str]

def validate_quality(state: ConcentrateState):
    # Business logic for blackberry concentrate inspection
    if state['brix_level'] > 60:
        return {'is_compliant': True, 'test_results': ['Brix valid', 'Sanitary check passed']}
    else:
        return {'is_compliant': False, 'test_results': ['Brix too low']}

def finish_processing(state: ConcentrateState):
    return {'test_results': state['test_results'] + ['Certification generated']}

graph = StateGraph(ConcentrateState)
graph.add_node('validate', validate_quality)
graph.add_node('finish', finish_processing)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph = graph.compile()
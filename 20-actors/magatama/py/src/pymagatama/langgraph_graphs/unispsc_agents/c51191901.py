from typing import TypedDict
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    grade: str
    test_results: dict
    approved: bool

def validate_quality(state: FeedState):
    protein = state['test_results'].get('protein', 0)
    moisture = state['test_results'].get('moisture', 100)
    is_valid = protein > 18 and moisture < 12
    return {'approved': is_valid}

graph_builder = StateGraph(FeedState)
graph_builder.add_node('qc_check', validate_quality)
graph_builder.add_edge('qc_check', END)
graph_builder.set_entry_point('qc_check')
graph = graph_builder.compile()
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class KIState(TypedDict):
    purity_level: float
    safety_clearance: bool
    batch_records: List[str]

def validate_quality(state: KIState):
    if state['purity_level'] >= 0.99:
        return {'safety_clearance': True}
    return {'safety_clearance': False}

def final_check(state: KIState):
    return 'Passed' if state['safety_clearance'] else 'Rejected'

graph = StateGraph(KIState)
graph.add_node('validate', validate_quality)
graph.add_node('final', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()
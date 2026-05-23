from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    commodity_code: str
    moisture: float
    safety_passed: bool
    log: list[str]

def validate_quality(state: FeedState):
    moisture = state['moisture']
    if moisture > 14.5:
        return {'safety_passed': False, 'log': ['Moisture too high']}
    return {'safety_passed': True, 'log': ['Quality check passed']}

def route_by_safety(state: FeedState):
    return 'process' if state['safety_passed'] else END

def process_logistics(state: FeedState):
    return {'log': state['log'] + ['Logistics initiated']}

graph = StateGraph(FeedState)
graph.add_node('validate', validate_quality)
graph.add_node('process', process_logistics)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety)
graph.add_edge('process', END)
graph = graph.compile()

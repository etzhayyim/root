from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoupState(TypedDict):
    temp: float
    has_haccp: bool
    is_expired: bool

def check_quality(state: SoupState):
    if state['temp'] > 5.0:
        return 'warning'
    return 'approved'

def check_compliance(state: SoupState):
    return 'compliant' if state['has_haccp'] else 'failed'

graph = StateGraph(SoupState)
graph.add_node('quality', check_quality)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('quality')
graph.add_edge('quality', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
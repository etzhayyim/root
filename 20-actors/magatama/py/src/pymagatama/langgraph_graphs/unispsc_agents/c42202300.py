from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IMRTState(TypedDict):
    device_id: str
    validation_checks: List[str]
    is_cleared: bool

def validate_physics(state: IMRTState):
    state['validation_checks'].append('Dose map verified')
    return {'validation_checks': state['validation_checks']}

def check_regulatory(state: IMRTState):
    state['is_cleared'] = True
    return {'is_cleared': state['is_cleared']}

graph = StateGraph(IMRTState)
graph.add_node('physics', validate_physics)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('physics')
graph.add_edge('physics', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
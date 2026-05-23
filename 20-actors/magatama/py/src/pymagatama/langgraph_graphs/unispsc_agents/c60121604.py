from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StudioState(TypedDict):
    items: List[str]
    validation_log: List[str]
    is_compliant: bool

def validate_accessory(state: StudioState):
    log = [item for item in state['items'] if 'capacity' in item]
    return {'validation_log': log, 'is_compliant': len(log) > 0}

def finalizer(state: StudioState):
    return {'is_compliant': True}

graph = StateGraph(StudioState)
graph.add_node('validate', validate_accessory)
graph.add_node('finalize', finalizer)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()

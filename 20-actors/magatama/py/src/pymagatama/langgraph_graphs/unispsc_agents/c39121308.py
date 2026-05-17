from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OutletBoxState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_specs(state: OutletBoxState):
    log = []
    if 'material' not in state['specs']: log.append('Missing Material')
    if 'ip_rating' not in state['specs']: log.append('Missing IP Rating')
    return {'validation_log': log, 'approved': len(log) == 0}

graph = StateGraph(OutletBoxState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
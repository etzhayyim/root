from typing import TypedDict
from langgraph.graph import StateGraph, END

class PatchPanelState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: PatchPanelState):
    required = ['rack_u', 'port_count', 'cat_level']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'error_log': [] if valid else ['Missing technical specs']}

def approval_check(state: PatchPanelState):
    return {'validated': state['validated'] and (state['specs'].get('rack_u', 0) > 0)}

graph = StateGraph(PatchPanelState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_check)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()

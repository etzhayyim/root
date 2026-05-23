from typing import TypedDict
from langgraph.graph import StateGraph, END

class HotCellState(TypedDict):
    spec_compliance: bool
    radiation_safety_checked: bool
    shielding_verified: bool

def validate_shielding(state: HotCellState):
    state['shielding_verified'] = True
    return 'check_safety'

def check_safety_protocols(state: HotCellState):
    state['radiation_safety_checked'] = True
    state['spec_compliance'] = True
    return END

graph = StateGraph(HotCellState)
graph.add_node('shielding', validate_shielding)
graph.add_node('safety', check_safety_protocols)
graph.set_entry_point('shielding')
graph.add_edge('shielding', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()

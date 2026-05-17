from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    pressure_ok: bool
    safety_check: bool
    finalized: bool

def validate_pressure(state: ToolState):
    state['pressure_ok'] = True
    return 'check_safety'

def check_safety(state: ToolState):
    state['safety_check'] = True
    return 'finalize'

def finalize_order(state: ToolState):
    state['finalized'] = True
    return END

graph = StateGraph(ToolState)
graph.add_node('validate', validate_pressure)
graph.add_node('check_safety', check_safety)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_safety')
graph.add_edge('check_safety', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
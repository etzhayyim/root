from typing import TypedDict
from langgraph.graph import StateGraph, END

class CanvasState(TypedDict):
    dimensions: str
    priming_type: str
    quality_check_passed: bool

def validate_canvas(state: CanvasState):
    state['quality_check_passed'] = bool(state.get('priming_type') and state.get('dimensions'))
    return state

def route_by_check(state: CanvasState):
    return 'process' if state['quality_check_passed'] else END

graph = StateGraph(CanvasState)
graph.add_node('validate', validate_canvas)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_check, {'process': 'process'})
graph.add_edge('process', END)
graph = graph.compile()

from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChalkLineState(TypedDict):
    line_length: float
    casing_material: str
    is_valid: bool

def validate_specs(state: ChalkLineState):
    state['is_valid'] = state['line_length'] > 0 and state['casing_material'] != ''
    return state

def determine_workflow(state: ChalkLineState):
    return 'process' if state['is_valid'] else END

def process_tool(state: ChalkLineState):
    print(f'Processing chalk line of length {state['line_length']}m')
    return state

graph = StateGraph(ChalkLineState)
graph.add_node('validation', validate_specs)
graph.add_node('process', process_tool)
graph.set_entry_point('validation')
graph.add_conditional_edges('validation', determine_workflow)
graph.add_edge('process', END)
compile = graph.compile()

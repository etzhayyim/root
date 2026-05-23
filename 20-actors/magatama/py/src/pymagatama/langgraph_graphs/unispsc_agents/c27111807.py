from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: ToolState):
    required = ['Flatness tolerance', 'Material']
    state['validated'] = all(k in state['spec_data'] for k in required)
    return state

def process_tool(state: ToolState):
    if state['validated']:
        print('Processing straight edge calibration request...')
    return state

graph = StateGraph(ToolState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_tool)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')

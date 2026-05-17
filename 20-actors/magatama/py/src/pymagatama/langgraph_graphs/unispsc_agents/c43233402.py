from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DataConversionState(TypedDict):
    input_format: str
    target_format: str
    validation_rules: List[str]
    is_approved: bool

def validate_formats(state: DataConversionState):
    state['is_approved'] = state['input_format'] != state['target_format']
    return state

def run_conversion(state: DataConversionState):
    print(f'Converting from {state['input_format']} to {state['target_format']}')
    return state

graph = StateGraph(DataConversionState)
graph.add_node('validate', validate_formats)
graph.add_node('convert', run_conversion)
graph.set_entry_point('validate')
graph.add_edge('validate', 'convert')
graph.add_edge('convert', END)
graph = graph.compile()
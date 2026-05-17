from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    pressure: float
    flow_rate: float
    verified: bool

def validate_specs(state: CompressorState):
    is_valid = state['pressure'] > 0 and state['flow_rate'] > 0
    return {'verified': is_valid}

def process_compressor(state: CompressorState):
    print(f'Processing compressor with flow: {state['flow_rate']}')
    return {'verified': True}

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_compressor)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
app = graph.compile()
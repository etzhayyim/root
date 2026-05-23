from typing import TypedDict
from langgraph.graph import StateGraph, END

class CompressorState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_pressure(state: CompressorState):
    pressure = state['spec_data'].get('pressure', 0)
    state['is_compliant'] = pressure > 0 and pressure <= 10.0
    return state

def inspection_log(state: CompressorState):
    print('Documenting pressure ratings and safety compliance for industrial compressor.')
    return state

graph = StateGraph(CompressorState)
graph.add_node('validate', validate_pressure)
graph.add_node('log', inspection_log)
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph.set_entry_point('validate')
graph = graph.compile()

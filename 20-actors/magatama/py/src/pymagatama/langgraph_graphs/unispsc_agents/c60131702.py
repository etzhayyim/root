from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiscoTapState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: DiscoTapState):
    required = ['input_voltage', 'signal_compatibility']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def process_procurement(state: DiscoTapState):
    print(f'Processing disco tap procurement: Validated={state['validated']}')
    return state

graph = StateGraph(DiscoTapState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
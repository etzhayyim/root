from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeState(TypedDict):
    spec: dict
    validated: bool

def validate_specs(state: TapeState):
    required = ['adhesive_type', 'width_mm', 'length_m']
    is_valid = all(k in state['spec'] for k in required)
    return {'validated': is_valid}

def process_procurement(state: TapeState):
    if state['validated']:
        print('Procurement spec validated: Ready for RFQ')
    return state

graph = StateGraph(TapeState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()

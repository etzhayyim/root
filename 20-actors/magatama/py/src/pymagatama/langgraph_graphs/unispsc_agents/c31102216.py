from typing import TypedDict
from langgraph.graph import StateGraph, END

class MoldState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_mold_spec(state: MoldState):
    required = ['purity_percentage', 'density_g_cm3']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

def process_casting_req(state: MoldState):
    return {'validation_passed': state['validation_passed']}

graph = StateGraph(MoldState)
graph.add_node('validate', validate_mold_spec)
graph.add_node('process', process_casting_req)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()

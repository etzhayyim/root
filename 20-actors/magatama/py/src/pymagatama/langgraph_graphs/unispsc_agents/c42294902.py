from typing import TypedDict
from langgraph.graph import StateGraph, END

class EndoscopeState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_medical_specs(state: EndoscopeState):
    required = ['sterilization_method', 'ISO_13485_certification']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def process_procurement(state: EndoscopeState):
    print('Processing endoscopic instrument procurement...')
    return state

graph = StateGraph(EndoscopeState)
graph.add_node('validate', validate_medical_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()

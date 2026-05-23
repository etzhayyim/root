from typing import TypedDict
from langgraph.graph import StateGraph, END

class UroAdapterState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_biocompatibility(state: UroAdapterState):
    bio_cert = state['spec_data'].get('biocompatibility')
    return {'validation_passed': bio_cert is not None}

def process_sterilization(state: UroAdapterState):
    print('Processing sterilization requirements...')
    return state

graph = StateGraph(UroAdapterState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('sterilize', process_sterilization)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterilize')
graph.add_edge('sterilize', END)
graph = graph.compile()

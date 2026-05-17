from typing import TypedDict
from langgraph.graph import StateGraph, END

class SalesCounterState(TypedDict):
    spec: dict
    approved: bool

def validate_specs(state: SalesCounterState):
    state['approved'] = 'material' in state['spec'] and 'dimensions' in state['spec']
    return state

def assembly_workflow(state: SalesCounterState):
    if state['approved']:
        print('Proceeding to manufacturing workflow')
    return state

graph = StateGraph(SalesCounterState)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assembly_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph = graph.compile()
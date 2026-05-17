from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BearingNutState(TypedDict):
    spec: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: BearingNutState):
    required = ['Thread Type', 'Material Grade']
    missing = [f for f in required if f not in state['spec']]
    return {'validation_results': [f'Missing: {m}' for m in missing], 'approved': len(missing) == 0}

def finish_node(state: BearingNutState):
    return {'validation_results': state['validation_results'] + ['Process Complete']}

graph = StateGraph(BearingNutState)
graph.add_node('validate', validate_specs)
graph.add_node('finish', finish_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph = graph.compile()
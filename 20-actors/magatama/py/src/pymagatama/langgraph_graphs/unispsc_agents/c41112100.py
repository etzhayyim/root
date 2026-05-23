from typing import TypedDict
from langgraph.graph import StateGraph, END

class TransducerState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_specs(state: TransducerState):
    specs = state['spec_data']
    results = []
    if 'accuracy_class' not in specs:
        results.append('Missing mandatory accuracy specification')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

graph = StateGraph(TransducerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

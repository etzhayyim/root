from typing import TypedDict
from langgraph.graph import StateGraph, END

class ImmobilizerState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_medical_spec(state: ImmobilizerState):
    fields = ['Material', 'WeightCapacity', 'RegulatoryID']
    results = [f for f in fields if f in state['spec_data']]
    return {'validation_results': results, 'is_compliant': len(results) == 3}

graph = StateGraph(ImmobilizerState)
graph.add_node('validate', validate_medical_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

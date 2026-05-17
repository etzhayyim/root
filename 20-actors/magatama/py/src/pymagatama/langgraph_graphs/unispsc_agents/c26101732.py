from typing import TypedDict
from langgraph.graph import StateGraph, END

class SparkPlugState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_specs(state: SparkPlugState):
    required = ['Thread size', 'Heat range']
    results = [f for f in required if f in state['spec_data']]
    return {'validation_results': results, 'is_approved': len(results) == len(required)}

def finalize_procurement(state: SparkPlugState):
    print('Procurement logic finalized')
    return {'is_approved': state['is_approved']}

graph = StateGraph(SparkPlugState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
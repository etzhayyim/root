from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BootState(TypedDict):
    specs: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: BootState):
    required = ['material', 'size', 'safety_rating']
    results = [field for field in required if field not in state['specs']]
    return {'validation_results': results, 'approved': len(results) == 0}

def approval_node(state: BootState):
    print(f'Checking compliance: {state.get('validation_results')}')
    return {'approved': state['approved']}

graph = StateGraph(BootState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)

compiled_graph = graph.compile()
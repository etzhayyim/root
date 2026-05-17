from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class MirrorState(TypedDict):
    specifications: dict
    validation_results: list[str]
    is_compliant: bool

def validate_optics(state: MirrorState):
    spec = state['specifications']
    results = []
    if spec.get('reflectivity', 0) < 95:
        results.append('Reflectivity too low for standard industrial grade')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

graph = StateGraph(MirrorState)
graph.add_node('validate', validate_optics)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
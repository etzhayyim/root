from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class WaistcoatState(TypedDict):
    specs: dict
    validation_results: Annotated[list, operator.add]

def validate_specs(state: WaistcoatState):
    results = []
    if not state['specs'].get('fabric'):
        results.append('Missing fabric composition')
    return {'validation_results': results}

def finalize_order(state: WaistcoatState):
    return {'validation_results': ['Approval granted']}

graph = StateGraph(WaistcoatState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()

from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class RelayState(TypedDict):
    spec: dict
    validation_results: list
    ready_for_procurement: bool

def validate_spec(state: RelayState):
    # Perform fine-grained validation of relay specs
    spec = state['spec']
    results = []
    if spec.get('switching_capacity', 0) < 5:
        results.append('Low capacity for industrial use')
    return {'validation_results': results}

def check_compliance(state: RelayState):
    ready = len(state['validation_results']) == 0
    return {'ready_for_procurement': ready}

graph = StateGraph(RelayState)
graph.add_node('validate', validate_spec)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()
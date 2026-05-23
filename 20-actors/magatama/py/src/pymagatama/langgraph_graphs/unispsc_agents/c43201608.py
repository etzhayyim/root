from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class NetworkState(TypedDict):
    task_id: str
    config: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_network_node(state: NetworkState):
    # Simulate network node validation logic
    node_id = state['config'].get('node_id')
    if node_id:
        return {'validation_log': [f'Validated node: {node_id}']}
    return {'validation_log': ['Invalid node configuration']}

def check_compliance(state: NetworkState):
    # Simulate compliance check
    return {'is_compliant': True}

graph = StateGraph(NetworkState)
graph.add_node('validate', validate_network_node)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

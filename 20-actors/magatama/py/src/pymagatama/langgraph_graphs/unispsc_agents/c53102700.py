from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class UniformState(TypedDict):
    order_id: str
    items: List[str]
    spec_verified: bool

def validate_specs(state: UniformState) -> UniformState:
    print(f'Validating specs for order {state[\"order_id\"]}')
    state[\"spec_verified\"] = True
    return state

def stage_shipment(state: UniformState) -> UniformState:
    print('Staging shipment for uniforms...')
    return state

graph = StateGraph(UniformState)
graph.add_node(\"validate\", validate_specs)
graph.add_node(\"stage\", stage_shipment)
graph.add_edge(\"validate\", \"stage\")
graph.add_edge(\"stage\", END)
graph.set_entry_point(\"validate\")
graph = graph.compile()
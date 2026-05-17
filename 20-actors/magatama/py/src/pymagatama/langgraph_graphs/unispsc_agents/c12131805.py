from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GasProcessState(TypedDict):
    commodity_code: str
    purity_level: float
    safety_clearance: bool
    shipping_log: Annotated[Sequence[str], operator.add]

def validate_gas_purity(state: GasProcessState):
    is_pure = state['purity_level'] >= 99.99
    return {'safety_clearance': is_pure, 'shipping_log': ['Purity validated' if is_pure else 'Purity check failed']}

def route_shipping(state: GasProcessState):
    if state['safety_clearance']:
        return 'ship'
    return 'quarantine'

graph = StateGraph(GasProcessState)
graph.add_node('validate', validate_gas_purity)
graph.add_node('ship', lambda s: {'shipping_log': ['Dispatching high-purity gas']})
graph.add_node('quarantine', lambda s: {'shipping_log': ['Gas quarantined for safety']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_shipping)
graph.add_edge('ship', END)
graph.add_edge('quarantine', END)
compiled_graph = graph.compile()
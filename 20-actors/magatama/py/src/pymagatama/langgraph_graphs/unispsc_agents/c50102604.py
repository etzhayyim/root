from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FrozenProduceState(TypedDict):
    product_name: str
    temp_log: List[float]
    is_compliant: bool

def validate_temp(state: FrozenProduceState):
    # Ensure storage remained below -18C
    state['is_compliant'] = all(t <= -18.0 for t in state['temp_log'])
    print(f'Temperature compliance status: {state['is_compliant']}')
    return state

def finalize_order(state: FrozenProduceState):
    print('Order processed based on cold chain integrity.')
    return state

graph = StateGraph(FrozenProduceState)
graph.add_node('validate', validate_temp)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
app = graph.compile()
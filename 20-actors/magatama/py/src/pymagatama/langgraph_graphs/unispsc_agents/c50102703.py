from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FrozenFruitState(TypedDict):
    batch_id: str
    temp_log: List[float]
    is_compliant: bool

def validate_cold_chain(state: FrozenFruitState):
    state['is_compliant'] = all(temp <= -18.0 for temp in state['temp_log'])
    print(f'Batch {state['batch_id']} compliance: {state['is_compliant']}')
    return 'end'

graph = StateGraph(FrozenFruitState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

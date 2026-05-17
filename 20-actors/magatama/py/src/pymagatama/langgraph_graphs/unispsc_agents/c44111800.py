from typing import TypedDict
from langgraph.graph import StateGraph, END

class DraftingSupplyState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: DraftingSupplyState):
    # Simulate CAD/Engineering standard validation logic
    required = ['accuracy', 'material']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def process_procurement(state: DraftingSupplyState):
    print(f'Processing procurement for {state[item_name]}')
    return state

graph = StateGraph(DraftingSupplyState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

# Compile
app = graph.compile()
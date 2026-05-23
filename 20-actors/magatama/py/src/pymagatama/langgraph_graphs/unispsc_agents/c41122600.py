from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabSupplyState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool

def validate_specs(state: LabSupplyState):
    # Simulate spec validation logic for microscope slides
    required = ['thickness', 'purity', 'certification']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def log_procurement(state: LabSupplyState):
    print(f'Processing procurement for: {state.get('item_name')}')
    return state

graph = StateGraph(LabSupplyState)
graph.add_node('validate', validate_specs)
graph.add_node('log', log_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
app = graph.compile()

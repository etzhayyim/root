from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    batch_id: str
    purity: float
    status: str
    validation_logs: List[str]

def validate_material(state: ProcessingState) -> ProcessingState:
    if state['purity'] >= 99.9:
        state['status'] = 'COMPLIANT'
        state['validation_logs'].append('Purity check passed.')
    else:
        state['status'] = 'REJECTED'
        state['validation_logs'].append('Purity below 99.9% threshold.')
    return state

def check_inventory(state: ProcessingState) -> ProcessingState:
    if state['status'] == 'COMPLIANT':
        state['status'] = 'READY_FOR_SHIPMENT'
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_material)
graph.add_node('inventory', check_inventory)
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph.set_entry_point('validate')
graph = graph.compile()
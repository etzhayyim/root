from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    item_id: str
    material_spec: str
    is_approved: bool

def validate_material(state: ProcessingState):
    # Simulate material check for chemical resistance
    approved = 'durable_plastic' in state['material_spec'].lower()
    return {'is_approved': approved}

def update_workflow(state: ProcessingState):
    return {'item_id': f'PROC-{state['item_id']}'}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_material)
graph.add_node('format', update_workflow)
graph.add_edge('validate', 'format')
graph.add_edge('format', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()

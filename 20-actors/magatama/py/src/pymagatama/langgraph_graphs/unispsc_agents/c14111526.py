from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class FolderProcurementState(TypedDict):
    material: str
    size: str
    quantity: int
    validation_log: Annotated[Sequence[str], operator.add]

def validate_material(state: FolderProcurementState):
    log = ['Material verified: Paper-based' if state['material'] == 'paper' else 'Invalid material']
    return {'validation_log': log}

def check_size(state: FolderProcurementState):
    log = ['Size compliant' if state['size'] in ['A4', 'Letter'] else 'Custom size required']
    return {'validation_log': log}

graph = StateGraph(FolderProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('size_check', check_size)
graph.set_entry_point('validate')
graph.add_edge('validate', 'size_check')
graph.add_edge('size_check', END)
compile = graph.compile()
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    part_id: str
    specs: dict
    validation_logs: List[str]
    approved: bool

def validate_material(state: PackagingState) -> PackagingState:
    state['validation_logs'].append('Checking material thermal stability.')
    return state

def check_compliance(state: PackagingState) -> PackagingState:
    state['validation_logs'].append('Verifying EMC and IP ratings.')
    state['approved'] = True
    return state

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

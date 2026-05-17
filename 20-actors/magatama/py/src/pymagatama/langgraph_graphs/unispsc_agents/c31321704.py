from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    part_id: str
    specs: dict
    validated: bool
    error_log: List[str]

def validate_material_certs(state: AssemblyState):
    print(f'Validating material certs for {state['part_id']}')
    return {'validated': True}

def check_dimensional_accuracy(state: AssemblyState):
    print(f'Checking tolerances for {state['part_id']}')
    return {'validated': state['validated'] and True}

graph = StateGraph(AssemblyState)
graph.add_node('cert_validation', validate_material_certs)
graph.add_node('dimension_check', check_dimensional_accuracy)
graph.set_entry_point('cert_validation')
graph.add_edge('cert_validation', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()
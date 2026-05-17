from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class KitState(TypedDict):
    part_numbers: List[str]
    compliance_ok: bool
    inspection_result: str

def validate_components(state: KitState):
    # Simulate CAD/BOM verification logic
    valid = all(p.startswith('ES-') for p in state['part_numbers'])
    return {'compliance_ok': valid}

def conduct_inspection(state: KitState):
    return {'inspection_result': 'PASS' if state['compliance_ok'] else 'FAIL'}

graph = StateGraph(KitState)
graph.add_node('validate', validate_components)
graph.add_node('inspect', conduct_inspection)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
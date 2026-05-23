from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ExtrusionState(TypedDict):
    part_id: str
    material_spec: str
    tolerance_check: bool
    passed: bool

def validate_specs(state: ExtrusionState):
    state['tolerance_check'] = True if len(state['material_spec']) > 5 else False
    return {'tolerance_check': state['tolerance_check']}

def final_approval(state: ExtrusionState):
    state['passed'] = state['tolerance_check']
    return {'passed': state['passed']}

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()

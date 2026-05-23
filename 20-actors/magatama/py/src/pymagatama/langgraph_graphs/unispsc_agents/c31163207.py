from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KeyState(TypedDict):
    part_number: str
    material: str
    tolerance_check: bool
    is_compliant: bool

def validate_specs(state: KeyState):
    is_compliant = state['material'] in ['AISI 4140', 'C1045'] and state['tolerance_check']
    return {'is_compliant': is_compliant}

def approval_step(state: KeyState):
    return {'is_compliant': True if state['is_compliant'] else False}

graph = StateGraph(KeyState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
app = graph.compile()

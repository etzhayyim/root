from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BiologicalState(TypedDict):
    resource_id: str
    inspection_status: str
    quarantine_clearance: bool
    log: List[str]

def validate_resource(state: BiologicalState) -> BiologicalState:
    if not state.get('resource_id'):
        state['log'].append('Invalid Resource ID')
    return state

def check_quarantine(state: BiologicalState) -> BiologicalState:
    state['quarantine_clearance'] = True
    state['log'].append('Quarantine check passed')
    return state

graph = StateGraph(BiologicalState)
graph.add_node('validate', validate_resource)
graph.add_node('quarantine', check_quarantine)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quarantine')
graph.add_edge('quarantine', END)
compiled_graph = graph.compile()

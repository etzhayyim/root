from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrumState(TypedDict):
    capacity: float
    has_un_certification: bool
    material_spec: str

def validate_certification(state: DrumState):
    if not state.get('has_un_certification'):
        print('Warning: Container missing UN certification for dangerous goods.')
    return 'validated'

def check_capacity(state: DrumState):
    return 'compliant' if state['capacity'] > 0 else 'error'

graph = StateGraph(DrumState)
graph.add_node('cert_check', validate_certification)
graph.add_node('cap_check', check_capacity)
graph.add_edge('cert_check', 'cap_check')
graph.add_edge('cap_check', END)
graph.set_entry_point('cert_check')
'graph' = graph.compile()
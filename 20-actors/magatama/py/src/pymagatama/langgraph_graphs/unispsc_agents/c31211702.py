from typing import TypedDict
from langgraph.graph import StateGraph, END

class LusterState(TypedDict):
    material_type: str
    firing_temp: int
    is_compliant: bool

def validate_temp(state: LusterState):
    state['is_compliant'] = 600 <= state['firing_temp'] <= 900
    return state

def check_msds(state: LusterState):
    print('Verifying chemical safety compliance...')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(LusterState)
graph.add_node('validate_firing', validate_temp)
graph.add_node('check_safety', check_msds)
graph.set_entry_point('validate_firing')
graph.add_edge('validate_firing', 'check_safety')
graph.add_edge('check_safety', END)
app = graph.compile()
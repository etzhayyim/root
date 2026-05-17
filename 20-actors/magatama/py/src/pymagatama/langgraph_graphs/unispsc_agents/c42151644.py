from langgraph.graph import StateGraph, END
from typing import TypedDict
class MouthPropState(TypedDict):
    material: str
    is_sterile: bool
    compliant: bool
def check_biocompatibility(state: MouthPropState):
    state['compliant'] = state['material'] in ['silicone', 'rubber']
    return state
def update_status(state: MouthPropState):
    return {'compliant': state['is_sterile'] and state['compliant']}
graph = StateGraph(MouthPropState)
graph.add_node('check_material', check_biocompatibility)
graph.add_node('verify_sterility', update_status)
graph.add_edge('check_material', 'verify_sterility')
graph.add_edge('verify_sterility', END)
graph.set_entry_point('check_material')
graph = graph.compile()
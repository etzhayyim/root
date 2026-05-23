from typing import TypedDict
from langgraph.graph import StateGraph, END

class MortuaryWrapState(TypedDict):
    material_specs: dict
    compliance_check: bool
    approved: bool

def validate_material(state: MortuaryWrapState):
    thickness = state['material_specs'].get('thickness', 0)
    return {'compliance_check': thickness >= 200}

def final_approval(state: MortuaryWrapState):
    return {'approved': state['compliance_check']}

graph = StateGraph(MortuaryWrapState)
graph.add_node('validate', validate_material)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')

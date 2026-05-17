from typing import TypedDict
from langgraph.graph import StateGraph, END
class DollPartState(TypedDict): 
    part_specs: dict
    is_safe: bool
    approved: bool
def validate_safety(state: DollPartState): 
    safety_certs = state['part_specs'].get('certifications', [])
    is_compliant = 'EN71' in safety_certs or 'ASTM F963' in safety_certs
    return {'is_safe': is_compliant}
def final_check(state: DollPartState): 
    return {'approved': state['is_safe']}

graph = StateGraph(DollPartState)
graph.add_node('safety_check', validate_safety)
graph.add_node('final_approval', final_check)
graph.add_edge('safety_check', 'final_approval')
graph.add_edge('final_approval', END)
graph.set_entry_point('safety_check')
graph = graph.compile()
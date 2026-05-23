from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IndustrialPartState(TypedDict):
    part_id: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: IndustrialPartState):
    log = ['Starting structural validation']
    compliance = all(k in state['specs'] for k in ['material', 'dimension'])
    log.append(f'Compliance: {compliance}')
    return {'is_compliant': compliance, 'validation_log': log}

def route_by_compliance(state: IndustrialPartState):
    return 'process_order' if state['is_compliant'] else 'flag_for_review'

graph = StateGraph(IndustrialPartState)
graph.add_node('validate', validate_specs)
graph.add_node('process_order', lambda s: {})
graph.add_node('flag_for_review', lambda s: {})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process_order', END)
graph.add_edge('flag_for_review', END)
compile_graph = graph.compile()

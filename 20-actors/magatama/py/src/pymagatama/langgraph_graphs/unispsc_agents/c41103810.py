from typing import TypedDict
from langgraph.graph import StateGraph, END
class StirrerState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str
def validate_specs(state: StirrerState):
    required = ['torque', 'speed_range']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Success' if valid else 'Missing specs'}
def finalize_procurement(state: StirrerState):
    return {'compliance_report': 'Finalized: ' + state['compliance_report']}
graph = StateGraph(StirrerState)
graph.add_node('validator', validate_specs)
graph.add_node('finalizer', finalize_procurement)
graph.add_edge('validator', 'finalizer')
graph.add_edge('finalizer', END)
graph.set_entry_point('validator')
graph = graph.compile()

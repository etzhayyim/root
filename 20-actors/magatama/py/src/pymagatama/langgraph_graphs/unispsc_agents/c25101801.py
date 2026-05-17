from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorcycleState(TypedDict):
    model_info: dict
    compliance_report: str
    validation_status: bool

def validate_specs(state: MotorcycleState):
    check = state['model_info'].get('displacement', 0) > 0
    return {'validation_status': check, 'compliance_report': 'Validated' if check else 'Invalid'}

def finalize_order(state: MotorcycleState):
    return {'compliance_report': 'Order Finalized'}

graph = StateGraph(MotorcycleState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MotorProcurementState(TypedDict):
    specs: dict
    validation_results: Annotated[Sequence[str], operator.add]
    status: str

def validate_specs(state: MotorProcurementState):
    specs = state['specs']
    results = []
    if 'holding_torque' not in specs: results.append('Missing holding_torque')
    if specs.get('ip_rating', 0) < 54: results.append('Insufficient IP rating')
    return {'validation_results': results}

def check_export_control(state: MotorProcurementState):
    return {'status': 'EXPORT_REVIEW_PENDING' if state['specs'].get('high_precision') else 'APPROVED'}

graph = StateGraph(MotorProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_control)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
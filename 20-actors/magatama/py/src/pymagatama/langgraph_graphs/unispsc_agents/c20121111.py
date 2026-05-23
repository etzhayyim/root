from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class RobotProcurementState(TypedDict):
    specs: dict
    validation_logs: Annotated[List[str], operator.add]
    status: str

def validate_specs(state: RobotProcurementState):
    specs = state['specs']
    logs = []
    if specs.get('repeatability_mm', 1.0) > 0.5:
        logs.append('Warning: Repeatability exceeds precision threshold.')
    return {'validation_logs': logs, 'status': 'VALIDATED' if not logs else 'NEEDS_REVIEW'}

def prepare_contract(state: RobotProcurementState):
    return {'status': 'CONTRACT_READY'}

graph = StateGraph(RobotProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('contract', prepare_contract)
graph.add_edge('validate', 'contract')
graph.add_edge('contract', END)
graph.set_entry_point('validate')
graph = graph.compile()

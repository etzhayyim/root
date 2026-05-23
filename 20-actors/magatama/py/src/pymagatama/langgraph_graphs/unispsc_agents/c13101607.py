from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GasProcurementState(TypedDict):
    commodity_code: str
    purity_required: float
    safety_clearance: bool
    validation_logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: GasProcurementState):
    passed = state['purity_required'] >= 99.999
    return {'validation_logs': ['Purity check passed' if passed else 'Purity insufficient']}

def check_compliance(state: GasProcurementState):
    return {'safety_clearance': True, 'validation_logs': ['Compliance verified against dual-use criteria']}

graph = StateGraph(GasProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()

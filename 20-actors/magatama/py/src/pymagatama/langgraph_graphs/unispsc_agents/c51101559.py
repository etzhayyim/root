from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class QualityControlState(TypedDict):
    material_id: str
    purity_validated: bool
    qc_logs: Annotated[Sequence[str], operator.add]

def validate_purity(state: QualityControlState):
    # Simulate analytical validation logic
    return {'purity_validated': True, 'qc_logs': ['Purity test passed for ' + state['material_id']]}

def generate_compliance_report(state: QualityControlState):
    return {'qc_logs': ['Compliance report generated successfully.']}

graph = StateGraph(QualityControlState)
graph.add_node('validate', validate_purity)
graph.add_node('report', generate_compliance_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
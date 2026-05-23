from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class MineralProcurementState(TypedDict):
    commodity_code: str
    purity_level: float
    certification_docs: List[str]
    compliance_score: float

def validate_purity(state: MineralProcurementState) -> MineralProcurementState:
    if state['purity_level'] < 0.999:
        state['compliance_score'] = 0.0
    else:
        state['compliance_score'] = 1.0
    return state

def check_export_compliance(state: MineralProcurementState) -> MineralProcurementState:
    # Logic to verify dual-use export control status
    return state

def aggregate_results(state: MineralProcurementState) -> Dict[str, Any]:
    return {'status': 'approved' if state['compliance_score'] > 0.5 else 'rejected'}

graph = StateGraph(MineralProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_export', check_export_compliance)
graph.add_node('aggregate', aggregate_results)

graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_export')
graph.add_edge('check_export', 'aggregate')
graph.add_edge('aggregate', END)

graph = graph.compile()

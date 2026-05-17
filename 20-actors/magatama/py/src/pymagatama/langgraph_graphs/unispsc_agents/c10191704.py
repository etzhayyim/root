from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SeedProcurementState(TypedDict):
    seed_id: str
    quality_metrics: dict
    compliance_checks: List[str]
    approved: bool

def validate_seed_quality(state: SeedProcurementState):
    metrics = state.get('quality_metrics', {})
    is_valid = metrics.get('germination_rate', 0) > 0.85
    return {'approved': is_valid}

def generate_compliance_report(state: SeedProcurementState):
    report = f'Compliance report for {state['seed_id']}: {'Pass' if state['approved'] else 'Fail'}'
    return {'compliance_checks': [report]}

graph = StateGraph(SeedProcurementState)
graph.add_node('validate', validate_seed_quality)
graph.add_node('report', generate_compliance_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
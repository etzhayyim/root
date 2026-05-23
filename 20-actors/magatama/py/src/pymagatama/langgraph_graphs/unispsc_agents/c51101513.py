from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class AntiepilepticState(TypedDict):
    lot_id: str
    temp_log: list[float]
    is_compliant: bool
    validation_steps: Annotated[Sequence[str], operator.add]

def validate_cold_chain(state: AntiepilepticState) -> AntiepilepticState:
    compliant = all(2.0 <= temp <= 8.0 for temp in state['temp_log'])
    return {'is_compliant': compliant, 'validation_steps': ['ColdChainValidation']}

def perform_quality_audit(state: AntiepilepticState) -> AntiepilepticState:
    if not state['is_compliant']:
        return {'validation_steps': ['AuditAborted-ColdChainFailure']}
    return {'validation_steps': ['QualityAuditPassed']}

graph = StateGraph(AntiepilepticState)
graph.add_node('validate_cold_chain', validate_cold_chain)
graph.add_node('quality_audit', perform_quality_audit)
graph.set_entry_point('validate_cold_chain')
graph.add_edge('validate_cold_chain', 'quality_audit')
graph.add_edge('quality_audit', END)
graph = graph.compile()

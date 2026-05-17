from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_id: str
    quality_checks: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_freshness(state: ProcurementState):
    print(f'Validating freshness for {state["commodity_id"]}')
    return {'quality_checks': ['freshness_verified']}

def check_compliance(state: ProcurementState):
    print(f'Checking quarantine compliance for {state["commodity_id"]}')
    return {'quality_checks': ['compliance_passed'], 'is_approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('freshness', validate_freshness)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('freshness')
graph.add_edge('freshness', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
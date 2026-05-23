from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystProcurementState(TypedDict):
    commodity_code: str
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: CatalystProcurementState):
    purity = state['spec_data'].get('purity_percentage', 0)
    if purity >= 99.0:
        return {'validation_logs': ['Purity check passed'], 'is_approved': True}
    return {'validation_logs': ['Purity check failed: below 99%'], 'is_approved': False}

def safety_compliance_check(state: CatalystProcurementState):
    if 'msds_version' in state['spec_data']:
        return {'validation_logs': ['Safety compliance verified']}
    return {'validation_logs': ['Safety compliance pending']}

graph = StateGraph(CatalystProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('safety_check', safety_compliance_check)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'safety_check')
graph.add_edge('safety_check', END)

app = graph.compile()

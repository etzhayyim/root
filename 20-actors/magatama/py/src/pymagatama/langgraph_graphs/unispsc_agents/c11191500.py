from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class CarbonIngestState(TypedDict):
    raw_data: dict
    purity_validated: bool
    compliance_cleared: bool
    analysis_logs: Annotated[List[str], add_messages]

def validate_purity(state: CarbonIngestState):
    purity = state['raw_data'].get('purity', 0)
    is_valid = purity >= 99.999
    return {'purity_validated': is_valid, 'analysis_logs': [f'Purity check: {purity}% - Validated: {is_valid}']}

def check_compliance(state: CarbonIngestState):
    is_compliant = state.get('purity_validated', False)
    return {'compliance_cleared': is_compliant, 'analysis_logs': [f'Export compliance cleared: {is_compliant}']}

graph = StateGraph(CarbonIngestState)
graph.add_node('purity_check', validate_purity)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()

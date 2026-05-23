from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CommodityState(TypedDict):
    commodity_id: str
    purity: float
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_purity(state: CommodityState):
    if state['purity'] >= 99.9:
        return {'validation_logs': ['Purity check passed: High-grade'], 'is_compliant': True}
    return {'validation_logs': ['Purity check failed: Below threshold'], 'is_compliant': False}

def security_protocol(state: CommodityState):
    if state['is_compliant']:
        return {'validation_logs': ['Security screening completed: Approved for procurement']}
    return {'validation_logs': ['Security screening failed: Manual review required']}

graph = StateGraph(CommodityState)
graph.add_node('purity_check', validate_purity)
graph.add_node('security_check', security_protocol)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'security_check')
graph.add_edge('security_check', END)
graph = graph.compile()

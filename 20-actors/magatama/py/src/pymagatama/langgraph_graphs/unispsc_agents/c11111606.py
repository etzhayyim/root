from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class NickelState(TypedDict):
    assay_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_nickel_purity(state: NickelState):
    purity = state['assay_data'].get('nickel_content_percent', 0)
    if purity >= 95.0:
        return {'validation_log': ['High purity verified'], 'is_approved': True}
    return {'validation_log': ['Purity below threshold'], 'is_approved': False}

def check_sanctions(state: NickelState):
    origin = state['assay_data'].get('origin_certification', '')
    if origin in ['CertifiedSafeZone']:
        return {'validation_log': ['Origin verified against sanctions list']}
    return {'validation_log': ['Origin requires manual review'], 'is_approved': False}

graph = StateGraph(NickelState)
graph.add_node('purity_check', validate_nickel_purity)
graph.add_node('sanctions_check', check_sanctions)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'sanctions_check')
graph.add_edge('sanctions_check', END)
graph = graph.compile()
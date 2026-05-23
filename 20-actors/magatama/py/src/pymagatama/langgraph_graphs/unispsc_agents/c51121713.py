from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class APIState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_report: List[str]

def validate_quality(state: APIState):
    if state['purity'] >= 99.0 and state['gmp_certified']:
        return {'compliance_report': ['Quality standards met']}
    return {'compliance_report': ['Quality check failed']}

graph = StateGraph(APIState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

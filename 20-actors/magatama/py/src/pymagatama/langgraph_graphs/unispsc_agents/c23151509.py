from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_compliance(state: WeldingGraphState):
    state['is_compliant'] = state['spec_data'].get('voltage') is not None
    return 'compliance_check'

def process_procurement(state: WeldingGraphState):
    print('Procurement logic for welding equipment initialized')
    return 'done'

graph = StateGraph(WeldingGraphState)
graph.add_node('validate', validate_compliance)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()

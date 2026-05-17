from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    spec_data: dict
    validation_report: List[str]
    is_approved: bool

def validate_lead_content(state: CastingState):
    content = state['spec_data'].get('lead_purity', 0)
    if content < 95.0:
        state['validation_report'].append('Purity below standard')
    return state

def check_dimensions(state: CastingState):
    if 'tolerance' not in state['spec_data']:
        state['validation_report'].append('Missing tolerance data')
    return state

graph = StateGraph(CastingState)
graph.add_node('validate_purity', validate_lead_content)
graph.add_node('check_dims', check_dimensions)
graph.add_edge('validate_purity', 'check_dims')
graph.add_edge('check_dims', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()
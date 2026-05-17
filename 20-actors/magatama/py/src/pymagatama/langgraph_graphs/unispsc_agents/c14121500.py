from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class PaperProcurementState(TypedDict):
    commodity_code: str
    spec_requirements: dict
    validation_logs: Annotated[List[str], add_messages]

def validate_quality(state: PaperProcurementState):
    spec = state['spec_requirements']
    logs = []
    if spec.get('basis_weight_gsm', 0) < 60:
        logs.append('Warning: Paper density below standard threshold')
    return {'validation_logs': logs}

def check_sustainability(state: PaperProcurementState):
    spec = state['spec_requirements']
    if not spec.get('fsc_certification_number'):
        return {'validation_logs': ['Error: Missing FSC certification']}
    return {'validation_logs': ['Sustainability criteria verified']}

builder = StateGraph(PaperProcurementState)
builder.add_node('validate', validate_quality)
builder.add_node('sustainability', check_sustainability)
builder.add_edge('validate', 'sustainability')
builder.add_edge('sustainability', END)
builder.set_entry_point('validate')
graph = builder.compile()
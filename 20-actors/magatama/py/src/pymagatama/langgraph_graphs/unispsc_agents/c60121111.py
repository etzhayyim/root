from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    paper_type: str
    weight_gsm: float
    is_acid_free: bool
    compliance_ok: bool

def validate_specs(state: PaperProcurementState):
    # Business logic for Sulphite paper quality checks
    min_weight = 120.0
    valid = state['weight_gsm'] >= min_weight and state['is_acid_free'] is True
    return {'compliance_ok': valid}

def finalize_procurement(state: PaperProcurementState):
    print(f'Procurement validated: {state['compliance_ok']}')
    return {'compliance_ok': state['compliance_ok']}

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
app = graph.compile()
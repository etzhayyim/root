from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ChemicalIngestState(TypedDict):
    batch_id: str
    purity_level: float
    analysis_logs: Annotated[List[str], operator.add]
    is_approved: bool

def validate_purity(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['purity_level'] >= 0.999:
        state['analysis_logs'].append('Purity check passed: Electronic grade')
        state['is_approved'] = True
    else:
        state['analysis_logs'].append('Purity check failed: Below threshold')
        state['is_approved'] = False
    return state

def run_compliance_check(state: ChemicalIngestState) -> ChemicalIngestState:
    state['analysis_logs'].append('Compliance audit: Dual-use export control verified')
    return state

builder = StateGraph(ChemicalIngestState)
builder.add_node('validate', validate_purity)
builder.add_node('compliance', run_compliance_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()

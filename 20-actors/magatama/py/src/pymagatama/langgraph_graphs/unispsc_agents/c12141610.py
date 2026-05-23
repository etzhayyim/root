from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ChemicalIngestState(TypedDict):
    material_id: str
    purity_level: float
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['purity_level'] < 0.9999:
        return {'validation_log': ['Purity level below standard'], 'is_approved': False}
    return {'validation_log': ['Purity check passed'], 'is_approved': True}

def audit_supply_chain(state: ChemicalIngestState) -> ChemicalIngestState:
    if state['is_approved']:
        return {'validation_log': ['Supply chain audit cleared']}
    return {'validation_log': ['Audit skipped due to failed validation']}

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_purity)
graph.add_node('audit', audit_supply_chain)
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('validate')
app = graph.compile()

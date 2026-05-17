from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalIngestState(TypedDict):
    material_id: str
    purity_level: float
    compliance_flags: Annotated[Sequence[str], operator.add]
    processing_steps: Annotated[Sequence[str], operator.add]

def validate_purity(state: ChemicalIngestState):
    if state['purity_level'] < 99.0:
        return {'compliance_flags': ['INSUFFICIENT_PURITY']}
    return {'compliance_flags': ['PURITY_VALIDATED']}

def prepare_logistics(state: ChemicalIngestState):
    return {'processing_steps': ['SDS_VERIFIED', 'HAZMAT_LABELING_APPLIED']}

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', prepare_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
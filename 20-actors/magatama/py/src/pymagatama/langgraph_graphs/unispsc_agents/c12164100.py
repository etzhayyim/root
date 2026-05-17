from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ChemicalIngestState(TypedDict):
    material_id: str
    purity_level: float
    compliance_checks: Annotated[List[str], operator.add]
    is_approved: bool

def validate_chemical_purity(state: ChemicalIngestState):
    if state['purity_level'] >= 99.9:
        return {'compliance_checks': ['Purity standard met'], 'is_approved': True}
    return {'compliance_checks': ['Purity standard failed'], 'is_approved': False}

def export_control_screening(state: ChemicalIngestState):
    return {'compliance_checks': ['Dual-use screening cleared']}

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_chemical_purity)
graph.add_node('screening', export_control_screening)
graph.set_entry_point('validate')
graph.add_edge('validate', 'screening')
graph.add_edge('screening', END)

# Compile the graph
app = graph.compile()
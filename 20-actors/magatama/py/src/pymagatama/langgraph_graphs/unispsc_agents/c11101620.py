from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ChemicalIngestState(TypedDict):
    chemical_id: str
    purity_level: float
    hazard_codes: List[str]
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_purity(state: ChemicalIngestState):
    threshold = 99.9
    if state['purity_level'] < threshold:
        return {'validation_logs': ['Purity level below threshold'], 'is_compliant': False}
    return {'validation_logs': ['Purity verification passed'], 'is_compliant': True}

def check_hazards(state: ChemicalIngestState):
    if 'TOXIC' in state['hazard_codes']:
        return {'validation_logs': ['Toxic hazard detected, trigger special handling'], 'is_compliant': False}
    return {'validation_logs': ['Hazard screening completed'], 'is_compliant': True}

graph = StateGraph(ChemicalIngestState)
graph.add_node('validate', validate_purity)
graph.add_node('hazard_check', check_hazards)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazard_check')
graph.add_edge('hazard_check', END)
graph = graph.compile()
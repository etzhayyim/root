from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from operator import add

class ChemicalState(TypedDict):
    material_id: str
    purity: float
    safety_verified: bool
    history: Annotated[List[str], add]

def validate_purity(state: ChemicalState) -> ChemicalState:
    if state['purity'] >= 99.9:
        return {'history': ['Purity validation passed']}
    else:
        return {'history': ['Purity insufficient', 'Rejecting']}

def safety_check(state: ChemicalState) -> ChemicalState:
    return {'safety_verified': True, 'history': ['SDS check complete']}

workflow = StateGraph(ChemicalState)
workflow.add_node('validate', validate_purity)
workflow.add_node('safety', safety_check)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'safety')
workflow.add_edge('safety', END)
graph = workflow.compile()
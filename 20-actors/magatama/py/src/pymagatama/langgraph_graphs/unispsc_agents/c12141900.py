from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    chemical_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_purity(state: ChemicalState) -> dict:
    purity = state['chemical_data'].get('purity', 0)
    if purity >= 99.0:
        return {'validation_results': ['Purity check passed'], 'is_approved': True}
    return {'validation_results': ['Purity check failed'], 'is_approved': False}

def check_compliance(state: ChemicalState) -> dict:
    if 'cas_number' in state['chemical_data']:
        return {'validation_results': ['Compliance check passed']}
    return {'validation_results': ['Missing CAS registry number']}

graph = StateGraph(ChemicalState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()
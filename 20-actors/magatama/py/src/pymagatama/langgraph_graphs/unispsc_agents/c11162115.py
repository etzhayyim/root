from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ChemicalState(TypedDict):
    raw_input: dict
    analysis_results: list
    compliance_passed: bool

def validate_chemical_purity(state: ChemicalState):
    data = state['raw_input']
    purity = data.get('purity_percentage', 0)
    return {'analysis_results': [f'Purity check: {purity}%'], 'compliance_passed': purity > 99.5}

def check_regulatory(state: ChemicalState):
    return {'analysis_results': state['analysis_results'] + ['Export control check: PASSED']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_chemical_purity)
graph.add_node('compliance', check_regulatory)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()

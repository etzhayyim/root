from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity: float
    safety_clearance: bool
    log: List[str]

def validate_chemical(state: ChemicalState):
    if state['purity'] < 0.99:
        return {'safety_clearance': False, 'log': state['log'] + ['Purity below threshold']}
    return {'safety_clearance': True, 'log': state['log'] + ['Purity validated']}

def perform_compliance_check(state: ChemicalState):
    # Simulated dual-use export control check
    return {'safety_clearance': True, 'log': state['log'] + ['Compliance check passed']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_chemical)
graph.add_node('compliance', perform_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

compiled_graph = graph.compile()
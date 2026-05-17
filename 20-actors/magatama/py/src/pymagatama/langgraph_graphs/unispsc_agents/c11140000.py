from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity: float
    compliance_docs: List[str]
    validation_passed: bool

def validate_chemical(state: ChemicalState):
    is_valid = state['purity'] >= 99.0 and len(state['compliance_docs']) > 0
    return {'validation_passed': is_valid}

def route_process(state: ChemicalState):
    if state['validation_passed']:
        return 'secure_log'
    return 'flag_review'

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_chemical)
graph.add_node('secure_log', lambda x: {'validation_passed': True})
graph.add_node('flag_review', lambda x: {'validation_passed': False})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_process)
graph.add_edge('secure_log', END)
graph.add_edge('flag_review', END)
graph = graph.compile()
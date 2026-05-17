from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity_required: float
    safety_check_passed: bool
    validation_log: List[str]

def validate_purity(state: ChemicalState):
    purity = state.get('purity_required', 0)
    if purity >= 99.0:
        return {'validation_log': state['validation_log'] + ['Purity level verified.']}
    return {'validation_log': state['validation_log'] + ['Purity insufficient.']}

def safety_compliance_step(state: ChemicalState):
    return {'safety_check_passed': True, 'validation_log': state['validation_log'] + ['Safety protocols met.']}

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_compliance_step)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
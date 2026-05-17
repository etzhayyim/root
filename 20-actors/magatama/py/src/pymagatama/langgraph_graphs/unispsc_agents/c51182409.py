from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity: float
    safety_clearance: bool
    validation_log: list

def validate_specs(state: ChemicalProcurementState):
    state['validation_log'] = []
    if state['purity'] >= 99.9:
        state['validation_log'].append('Purity check passed')
    return state

def check_regulatory(state: ChemicalProcurementState):
    state['safety_clearance'] = True
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
app = graph.compile()
from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_log: Annotated[list, operator.add]
    is_compliant: bool

def validate_concentration(state: ProcurementState):
    conc = state['spec_data'].get('concentration', 0)
    if 0.1 <= conc <= 11.0:
        return {'validation_log': ['Concentration within safe topical levels'], 'is_compliant': True}
    return {'validation_log': ['Concentration outside safe limits'], 'is_compliant': False}

def check_regulatory_status(state: ProcurementState):
    if state['spec_data'].get('license'):
        return {'validation_log': ['Regulatory license verified']}
    return {'is_compliant': False, 'validation_log': ['Missing regulatory license']}

graph = StateGraph(ProcurementState)
graph.add_node('val_conc', validate_concentration)
graph.add_node('val_reg', check_regulatory_status)
graph.set_entry_point('val_conc')
graph.add_edge('val_conc', 'val_reg')
graph.add_edge('val_reg', END)

app = graph.compile()

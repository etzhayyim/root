from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class OsmometerState(TypedDict):
    spec_data: dict
    validation_errors: Annotated[list, operator.add]
    is_compliant: bool

def validate_osmometer_specs(state: OsmometerState):
    errors = []
    if state['spec_data'].get('range', 0) <= 0:
        errors.append('Invalid measurement range.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

defroutetask(state: OsmometerState):
    return 'compliance_check'

graph = StateGraph(OsmometerState)
graph.add_node('validate', validate_osmometer_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
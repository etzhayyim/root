from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ActuatorState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    specs = state['spec_data']
    logs = []
    if specs.get('backlash_arcmin', 0) > 5:
        logs.append('Warning: High backlash detected')
    return {'validation_logs': logs}

def check_compliance(state: ActuatorState):
    is_compliant = 'certification_iso_10218' in state['spec_data']
    return {'is_compliant': is_compliant}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

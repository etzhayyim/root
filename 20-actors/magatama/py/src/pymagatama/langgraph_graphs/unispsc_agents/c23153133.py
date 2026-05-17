from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_requirements: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    specs = state['spec_requirements']
    logs = []
    if specs.get('repeatability_microns', 100) > 50:
        logs.append('Warning: High repeatability value detected.')
    return {'validation_logs': logs, 'is_compliant': True}

def check_compliance(state: ActuatorState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
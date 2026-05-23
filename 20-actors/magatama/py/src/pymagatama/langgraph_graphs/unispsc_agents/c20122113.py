from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class VFDState(TypedDict):
    spec_requirements: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_vfd_specs(state: VFDState):
    specs = state['spec_requirements']
    logs = []
    compliant = True
    if specs.get('voltage', 0) < 200:
        logs.append('Voltage below minimum industrial threshold')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def route_to_testing(state: VFDState):
    return 'testing' if state['is_compliant'] else END

workflow = StateGraph(VFDState)
workflow.add_node('validation', validate_vfd_specs)
workflow.add_node('testing', lambda s: {'validation_logs': ['Hardware stress test passed']})
workflow.set_entry_point('validation')
workflow.add_conditional_edges('validation', route_to_testing)
workflow.add_edge('testing', END)
graph = workflow.compile()

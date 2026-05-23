from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: BearingState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if 'load_rating' not in specs:
        logs.append('Missing load rating')
        compliant = False
    return {'validation_log': logs, 'is_compliant': compliant}

def route_verification(state: BearingState):
    return 'process' if state['is_compliant'] else END

workflow = StateGraph(BearingState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', route_verification, {'process': 'process', '__end__': END})
workflow.add_node('process', lambda s: {'validation_log': ['Proceeding with procurement workflow']})
workflow.add_edge('process', END)
graph = workflow.compile()

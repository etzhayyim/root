from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: TractorState):
    log = []
    compliant = True
    if state['specs'].get('engine_power_hp', 0) < 50:
        log.append('Power requirement below minimum threshold.')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

workflow = StateGraph(TractorState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
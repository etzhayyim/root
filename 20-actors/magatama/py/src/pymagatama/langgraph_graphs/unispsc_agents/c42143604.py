from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HeadRestraintState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: HeadRestraintState):
    log = []
    compliant = True
    if 'Material_Biocompatibility_Report' not in state['specs']:
        log.append('Missing biocompatibility certification.')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def route_by_compliance(state: HeadRestraintState):
    return 'compliant' if state['is_compliant'] else 'rejected'

graph = StateGraph(HeadRestraintState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'rejected': END})
graph.compile()
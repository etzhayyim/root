from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec: dict
    validation_result: bool
    log: Annotated[list[str], operator.add]

def validate_bearing(state: BearingState):
    spec = state['spec']
    valid = all(k in spec for k in ['outer', 'inner', 'load'])
    return {'validation_result': valid, 'log': ['Validation complete']}

def check_compliance(state: BearingState):
    if state['validation_result']:
        return {'log': ['Compliance check passed']}
    return {'log': ['Compliance check failed']}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_bearing)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

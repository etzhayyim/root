from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class LubricantState(TypedDict):
    lubricant_spec: dict
    validation_log: Annotated[list[str], add_messages]
    is_approved: bool

def validate_viscosity(state: LubricantState) -> LubricantState:
    spec = state['lubricant_spec']
    if 32 <= spec.get('viscosity', 0) <= 680:
        state['validation_log'].append('Viscosity validated.')
    else:
        state['validation_log'].append('Viscosity out of standard range.')
    return state

def check_compliance(state: LubricantState) -> LubricantState:
    if state['lubricant_spec'].get('msds_ready', False):
        state['is_approved'] = True
        state['validation_log'].append('Compliance checks passed.')
    else:
        state['is_approved'] = False
        state['validation_log'].append('Compliance checks failed.')
    return state

graph = StateGraph(LubricantState)
graph.add_node('validate', validate_viscosity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
compile_graph = graph.compile()
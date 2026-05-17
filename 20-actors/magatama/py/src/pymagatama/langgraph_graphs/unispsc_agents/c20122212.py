from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class LubricantState(TypedDict):
    spec_requirements: dict
    inspection_results: Annotated[Sequence[str], operator.add]
    approval_status: str

def validate_viscosity(state: LubricantState) -> dict:
    if 'viscosity_grade' not in state['spec_requirements']:
        return {'inspection_results': ['Viscosity missing']}
    return {'inspection_results': ['Viscosity valid']}

def safety_check(state: LubricantState) -> dict:
    return {'inspection_results': ['SDS verified']}

graph = StateGraph(LubricantState)
graph.add_node('validate', validate_viscosity)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
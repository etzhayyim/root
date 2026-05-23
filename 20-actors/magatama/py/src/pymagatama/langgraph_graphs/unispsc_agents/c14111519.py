from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PaperState(TypedDict):
    spec: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: PaperState):
    s = state['spec']
    res = []
    if s.get('gsm_weight', 0) < 40: res.append('Weight too low')
    if not s.get('thermal_coating_type'): res.append('Coating missing')
    return {'validation_results': res, 'is_compliant': len(res) == 0}

graph = StateGraph(PaperState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()

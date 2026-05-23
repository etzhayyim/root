from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GasState(TypedDict):
    commodity_code: str
    purity_level: float
    pressure: float
    safety_check_passed: bool
    logs: Annotated[Sequence[str], operator.add]

def validate_composition(state: GasState):
    if state['purity_level'] < 0.99:
        return {'logs': ['Purity low, triggering re-refinement']}
    return {'logs': ['Purity acceptable']}

def check_infrastructure(state: GasState):
    if state['pressure'] > 5000:
        return {'logs': ['Pressure exceeding safety limits'], 'safety_check_passed': False}
    return {'logs': ['Infrastructure secure'], 'safety_check_passed': True}

graph = StateGraph(GasState)
graph.add_node('validate', validate_composition)
graph.add_node('safety', check_infrastructure)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()

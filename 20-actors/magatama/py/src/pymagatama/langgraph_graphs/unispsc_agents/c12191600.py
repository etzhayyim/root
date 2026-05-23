from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AlkylatingAgentState(TypedDict):
    agent_id: str
    purity_level: float
    hazard_checks: Annotated[Sequence[str], operator.add]
    validation_passed: bool

def validate_purity(state: AlkylatingAgentState):
    is_pure = state['purity_level'] >= 99.5
    return {'validation_passed': is_pure, 'hazard_checks': ['purity_check_done']}

def check_regulations(state: AlkylatingAgentState):
    return {'hazard_checks': ['compliance_check_passed']}

graph = StateGraph(AlkylatingAgentState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_regulations', check_regulations)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_regulations')
graph.add_edge('check_regulations', END)
graph = graph.compile()

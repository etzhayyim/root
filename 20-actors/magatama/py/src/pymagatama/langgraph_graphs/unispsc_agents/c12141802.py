from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity: float
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_purity(state: CatalystState):
    is_valid = state['purity'] >= 99.5
    return {'validation_log': [f'Purity check: {is_valid}'], 'status': 'valid' if is_valid else 'rejected'}

def check_hazard(state: CatalystState):
    return {'validation_log': ['Hazard assessment: Reviewing MSDS for reactivity limits']}

def process_deployment(state: CatalystState):
    return {'validation_log': ['Deployment: Ready for industrial reactor integration']}

graph = StateGraph(CatalystState)
graph.add_node('validate', validate_purity)
graph.add_node('hazard', check_hazard)
graph.add_node('deploy', process_deployment)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazard')
graph.add_edge('hazard', 'deploy')
graph.add_edge('deploy', END)

compile_graph = graph.compile()

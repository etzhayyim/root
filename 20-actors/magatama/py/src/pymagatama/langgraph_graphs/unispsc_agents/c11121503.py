from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CeramicState(TypedDict):
    material_id: str
    purity: float
    steps: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_purity(state: CeramicState):
    compliant = state['purity'] >= 99.9
    return {'is_compliant': compliant, 'steps': ['purity_check_passed' if compliant else 'purity_failed']}

def process_material(state: CeramicState):
    return {'steps': ['material_processing_complete']}

def router(state: CeramicState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(CeramicState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_material)
graph.add_edge('validate', 'process')
graph.add_conditional_edges('validate', router, {'process': 'process', '__end__': END})
graph.set_entry_point('validate')
graph.add_edge('process', END)
graph = graph.compile()
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity_level: float
    safety_clearance: bool
    batch_data: dict
    workflow_log: List[str]

def validate_purity(state: ChemicalState):
    is_pure = state['purity_level'] >= 0.999
    return {'safety_clearance': is_pure, 'workflow_log': state['workflow_log'] + ['Purity validation complete']}

def process_dangerous_goods(state: ChemicalState):
    return {'workflow_log': state['workflow_log'] + ['Safety protocols engaged for transport']}

def compile_graph():
    graph = StateGraph(ChemicalState)
    graph.add_node('validate_purity', validate_purity)
    graph.add_node('process_dangerous_goods', process_dangerous_goods)
    graph.set_entry_point('validate_purity')
    graph.add_edge('validate_purity', 'process_dangerous_goods')
    graph.add_edge('process_dangerous_goods', END)
    return graph.compile()

graph = compile_graph()
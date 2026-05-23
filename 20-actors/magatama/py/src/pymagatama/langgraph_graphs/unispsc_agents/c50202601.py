from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class JuiceState(TypedDict):
    product_name: str
    quality_docs: List[str]
    is_compliant: bool

def validate_food_standards(state: JuiceState):
    # Business logic for apple juice compliance
    compliant = all([doc in state['quality_docs'] for doc in ['HACCP', 'FSSC22000']])
    return {'is_compliant': compliant}

def route_by_compliance(state: JuiceState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(JuiceState)
graph.add_node('validate', validate_food_standards)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': 'process'})
graph.add_edge('process', END)
graph.compile()

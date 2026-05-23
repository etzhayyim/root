from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    part_id: str
    specs: dict
    validated: bool
    export_control_check: bool

def validate_materials(state: TitaniumState):
    grade = state['specs'].get('grade')
    return {'validated': grade in ['Grade 2', 'Grade 5']}

def check_compliance(state: TitaniumState):
    return {'export_control_check': True}

graph = StateGraph(TitaniumState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()

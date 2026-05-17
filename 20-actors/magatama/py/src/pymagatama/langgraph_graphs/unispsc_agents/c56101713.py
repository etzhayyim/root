from typing import TypedDict
from langgraph.graph import StateGraph, END

class DeskState(TypedDict):
    specs: dict
    validated: bool

def validate_desk_specs(state: DeskState):
    required = ['material', 'dimensions', 'load_limit']
    all_present = all(k in state['specs'] for k in required)
    return {'validated': all_present}

def assembly_instruction_check(state: DeskState):
    return {'validated': state['validated'] and "manual_included" in state['specs']}

graph = StateGraph(DeskState)
graph.add_node("validate", validate_desk_specs)
graph.add_node("assembly", assembly_instruction_check)
graph.set_entry_point("validate")
graph.add_edge("validate", "assembly")
graph.add_edge("assembly", END)
graph = graph.compile()
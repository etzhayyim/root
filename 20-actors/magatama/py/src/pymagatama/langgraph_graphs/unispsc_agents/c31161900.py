from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpringProcureState(TypedDict):
    material: str
    spring_rate: float
    load_capacity: float

def validate_engineering_specs(state: SpringProcureState):
    print(f'Validating spring rate: {state['spring_rate']}')
    return {'status': 'validated'}

def check_material_compliance(state: SpringProcureState):
    print(f'Checking material: {state['material']}')
    return {'compliance': 'certified'}

workflow = StateGraph(SpringProcureState)
workflow.add_node('validate', validate_engineering_specs)
workflow.add_node('compliance', check_material_compliance)
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
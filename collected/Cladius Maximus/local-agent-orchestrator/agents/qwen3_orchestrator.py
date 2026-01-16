"""
Qwen3 Orchestrator Agent for Local Coding
This agent coordinates and manages other coding agents in a local environment.
"""
import json
import os
import sys
from typing import Dict, List, Any

# Add the project root to the path to access other agents
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.base_agent import BaseAgent

class Qwen3OrchestratorAgent(BaseAgent):
    def __init__(self, name: str = "Qwen3_Orchestrator"):
        super().__init__(name)
        self.task_queue = []
        self.active_tasks = {}
        self.agent_registry = {
            'code_planner': 'Code Planner',
            'implementation': 'Implementation Agent',
            'code_reviewer': 'Code Reviewer'
        }
    
    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the main orchestrator task - manage the workflow
        """
        try:
            # Extract task parameters
            task_type = task_context.get('task_type', 'default_task')
            task_details = task_context.get('task_details', {})
            
            if task_type == 'workflow_execution':
                # Handle workflow execution
                workflow_steps = self._process_workflow(task_details)
                return {
                    "status": "completed",
                    "task_type": task_type,
                    "results": workflow_steps,
                    "message": "Workflow completed successfully"
                }
            elif task_type == 'task_assignment':
                # Assign task to appropriate agent
                assigned_task = self._assign_task(task_details)
                return {
                    "status": "assigned",
                    "task_type": task_type,
                    "assigned_to": assigned_task.get('agent', 'unknown'),
                    "task_details": assigned_task,
                    "message": "Task assigned successfully"
                }
            else:
                # Default task handling
                response = self._handle_default_task(task_details)
                return {
                    "status": "completed",
                    "task_type": task_type,
                    "results": response,
                    "message": "Task handled successfully"
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Orchestrator failed to execute task"
            }
    
    def _process_workflow(self, workflow_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a complex workflow with multiple steps
        """
        steps = []
        workflow_plan = workflow_details.get('plan', [])
        
        for i, step in enumerate(workflow_plan):
            try:
                agent_name = step.get('agent', 'unknown')
                step_description = step.get('description', 'No description')
                
                # Simulate agent execution
                execution_result = {
                    "step": i + 1,
                    "agent": agent_name,
                    "description": step_description,
                    "status": "completed",
                    "timestamp": self.get_timestamp()
                }
                steps.append(execution_result)
                
            except Exception as e:
                steps.append({
                    "step": i + 1,
                    "agent": agent_name,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": self.get_timestamp()
                })
        
        return steps
    
    def _assign_task(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assign a task to the most appropriate agent based on task type
        """
        task_type = task_details.get('type', 'general')
        
        # Simple task assignment logic
        if task_type == 'coding':
            agent = 'implementation'
            description = "Implement new functionality or feature"
        elif task_type == 'analysis':
            agent = 'code_planner'
            description = "Analyze code structure and requirements"
        elif task_type == 'review':
            agent = 'code_reviewer'
            description = "Review code quality and security"
        elif task_type == 'refactor':
            agent = 'implementation'
            description = "Refactor existing code"
        else:
            agent = 'code_planner'
            description = "General code planning task"
        
        return {
            "agent": agent,
            "task_type": task_type,
            "description": description,
            "details": task_details
        }
    
    def _handle_default_task(self, task_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle a default or generic task
        """
        return {
            "response": f"Orchestrator processing: {task_details.get('description', 'No description')}",
            "agents_involved": list(self.agent_registry.keys()),
            "recommendation": "Please specify more detailed task instructions"
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get the current status of the orchestrator and registered agents
        """
        return {
            "orchestrator": {
                "name": self.name,
                "status": "active",
                "registered_agents": list(self.agent_registry.keys()),
                "task_queue": len(self.task_queue)
            },
            "agents": {
                agent: {
                    "status": "available",
                    "type": description
                }
                for agent, description in self.agent_registry.items()
            }
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Return detailed information about this agent
        """
        return {
            "name": self.name,
            "type": "orchestrator",
            "description": "Qwen3-based orchestrator that manages workflow between specialized coding agents",
            "capabilities": [
                "Workflow management",
                "Task assignment",
                "Task coordination",
                "Status monitoring"
            ],
            "interfaces": {
                "input": "task_context (dict)",
                "output": "execution_results (dict)"
            }
        }

# Example usage
if __name__ == "__main__":
    orchestrator = Qwen3OrchestratorAgent()
    status = orchestrator.get_agent_status()
    print(json.dumps(status, indent=2))
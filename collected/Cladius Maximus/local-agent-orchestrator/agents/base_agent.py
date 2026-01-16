"""
Base Agent Class for Local Agent Orchestrator
This provides a common interface and functionality for all agent types in the system.
"""
import json
import os
import sys
from typing import Dict, List, Any, Optional

class BaseAgent:
    """
    Base class for all agents in the local agent orchestrator system.
    All specific agents should inherit from this class.
    """
    
    def __init__(self, name: str = "BaseAgent"):
        self.name = name
        self.version = "1.0.0"
        self.status = "initialized"
        
    def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task with the given context.
        This method should be overridden by child classes.
        """
        raise NotImplementedError("Child classes must implement execute_task method")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """
        Get the current status of the agent.
        Should be overridden by child classes.
        """
        return {
            "name": self.name,
            "type": "base_agent",
            "status": self.status,
            "version": self.version
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get detailed information about this agent.
        Should be overridden by child classes.
        """
        return {
            "name": self.name,
            "type": "base_agent",
            "description": "Base agent class for local agent orchestrator",
            "version": self.version,
            "capabilities": [
                "Task execution",
                "Status reporting",
                "Information retrieval"
            ]
        }
    
    def validate_task_context(self, task_context: Dict[str, Any]) -> bool:
        """
        Validate that the task context contains required fields.
        """
        required_fields = ['task_type', 'task_details']
        for field in required_fields:
            if field not in task_context:
                return False
        return True
    
    def format_result(self, status: str, task_type: str, results: Any, message: str = "") -> Dict[str, Any]:
        """
        Format a standardized result for agent execution.
        """
        return {
            "status": status,
            "task_type": task_type,
            "results": results,
            "message": message,
            "agent": self.name
        }
    
    def log_execution(self, task_type: str, results: Any):
        """
        Log the execution of a task (placeholder for actual logging).
        """
        print(f"[{self.name}] Executed {task_type}: {results}")
    
    def __str__(self):
        return f"Agent({self.name}, {self.status})"

# Example usage
if __name__ == "__main__":
    # Create a simple test agent that inherits from BaseAgent
    class TestAgent(BaseAgent):
        def __init__(self):
            super().__init__("TestAgent")
        
        def execute_task(self, task_context: Dict[str, Any]) -> Dict[str, Any]:
            return self.format_result(
                status="completed",
                task_type=task_context.get('task_type', 'unknown'),
                results={"message": "Test execution completed"},
                message="Test agent executed successfully"
            )
        
        def get_agent_status(self) -> Dict[str, Any]:
            return {
                "name": self.name,
                "type": "test_agent",
                "status": "ready",
                "version": self.version,
                "capabilities": ["test_execution"]
            }
        
        def get_agent_info(self) -> Dict[str, Any]:
            return {
                "name": self.name,
                "type": "test",
                "description": "Test agent for demonstrating base class functionality",
                "version": self.version,
                "capabilities": ["task_execution", "status_check", "information_retrieval"]
            }
    
    # Test the base agent functionality
    test_agent = TestAgent()
    status = test_agent.get_agent_status()
    print(json.dumps(status, indent=2))
    
    result = test_agent.execute_task({"task_type": "test", "task_details": {}})
    print(json.dumps(result, indent=2))
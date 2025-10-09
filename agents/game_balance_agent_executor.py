from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.types import TaskStatusUpdateEvent, TaskArtifactUpdateEvent, TaskStatus, TaskState, Artifact, TextPart
import json
import re

class GameBalanceExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue):
        from game_balance_agent import agent
        
        input_text = context.message.parts[0].root.text
        
        # Get conversation history
        history = []
        if context.current_task and context.current_task.artifacts:
            for artifact in context.current_task.artifacts:
                if artifact.parts:
                    history.append(artifact.parts[0].root.text)
        
        # Build context with history
        if history:
            full_input = f"Previous conversation:\n" + "\n".join(history[-6:]) + f"\n\nCurrent question: {input_text}"
        else:
            full_input = input_text
        
        try:
            result = await agent.invoke_async(full_input)
            response = result.output if hasattr(result, 'output') else str(result)
            
            # Parse JSON response
            clean_response = re.sub(r'<thinking>.*?</thinking>', '', response, flags=re.DOTALL).strip()
            
            try:
                json_match = re.search(r'\{[^}]*"status"[^}]*"message"[^}]*\}', clean_response, re.DOTALL)
                if json_match:
                    response_json = json.loads(json_match.group())
                    status = response_json.get('status', 'completed')
                    message = response_json.get('message', clean_response)
                else:
                    status = 'completed'
                    message = clean_response
            except:
                status = 'completed'
                message = clean_response
            
            # Map status to TaskState
            state_map = {
                'completed': TaskState.COMPLETED,
                'input_required': TaskState.INPUT_REQUIRED,
                'error': TaskState.FAILED
            }
            task_state = state_map.get(status, TaskState.COMPLETED)
            
            # Send status update
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                taskId=context.current_task.id,
                contextId=context.context_id,
                status=TaskStatus(state=task_state),
                final=(task_state != TaskState.INPUT_REQUIRED)
            ))
            
            # Send artifact with full JSON response
            full_response = json.dumps({"status": status, "message": message}, ensure_ascii=False)
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                taskId=context.current_task.id,
                contextId=context.context_id,
                artifact=Artifact(
                    artifactId=f"response-{context.current_task.id}",
                    parts=[TextPart(text=full_response)]
                )
            ))
            
        except Exception as e:
            await event_queue.enqueue_event(TaskStatusUpdateEvent(
                taskId=context.current_task.id,
                contextId=context.context_id,
                status=TaskStatus(state=TaskState.FAILED),
                final=True
            ))
            
            error_response = json.dumps({"status": "error", "message": f"오류 발생: {str(e)}"}, ensure_ascii=False)
            await event_queue.enqueue_event(TaskArtifactUpdateEvent(
                taskId=context.current_task.id,
                contextId=context.context_id,
                artifact=Artifact(
                    artifactId=f"error-{context.current_task.id}",
                    parts=[TextPart(text=error_response)]
                )
            ))
    
    async def cancel(self, context: RequestContext):
        pass

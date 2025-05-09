# app.py
import os
import time
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
import boto3
import weave
from typing import Union
import asyncio

SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
AGENT_ID        = os.environ["AGENT_ID"]
AGENT_ALIAS_ID  = os.environ["AGENT_ALIAS_ID"]
REGION          = os.getenv("AWS_REGION")

app = AsyncApp(token=SLACK_BOT_TOKEN)
br_client = boto3.client("bedrock-agent-runtime", region_name=REGION)

@weave.op()
def invoke_bedrock_agent(user_input: str, mode: str = "normal") -> Union[str, dict]:
    """Invoke Bedrock agent and return the response.
    
    Args:
        user_input: The user's input text
        mode: The mode of operation ("normal" or "eval")
        
    Returns:
        Union[str, dict]: The agent's response, either as a string or a dict containing result and eval info
    """
    try:
        if mode == "normal":
            stream = br_client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=str(time.time()),
                inputText=user_input,
                enableTrace=False
            )
        elif mode == "eval":
            stream = br_client.invoke_agent(
                agentId=AGENT_ID,
                agentAliasId=AGENT_ALIAS_ID,
                sessionId=str(time.time()),
                inputText=user_input,
                enableTrace=True
            )
        else:
            raise ValueError(f"Invalid mode: {mode}")

        chunks = []
        eval_info = []
        
        def extract_action_info(event):
            if not event or "trace" not in event:
                return None
                
            try:
                trace_data = event["trace"]
                if "trace" in trace_data and "orchestrationTrace" in trace_data["trace"]:
                    trace = trace_data["trace"]["orchestrationTrace"]
                    
                    if "invocationInput" in trace:
                        invocation = trace["invocationInput"]
                        if "actionGroupInvocationInput" in invocation:
                            action_input = invocation["actionGroupInvocationInput"]
                            return {
                                "type": "action",
                                "action_group": action_input["actionGroupName"],
                                "function": action_input["function"],
                                "parameters": action_input["parameters"]
                            }
                    
                    if "modelInvocationInput" in trace:
                        model_input = trace["modelInvocationInput"]
                        return {
                            "type": "model",
                            "model": model_input["foundationModel"],
                            "config": model_input["inferenceConfiguration"]
                        }
            except Exception as e:
                print(f"Error extracting action info: {e}")
            return None

        for event in stream["completion"]:
            if not event:  # Skip None chunks
                continue
                
            try:
                if mode == "eval":
                    action_info = extract_action_info(event)
                    if action_info:
                        if action_info["type"] == "action":
                            info_str = "\n=== Action Info ===\n"
                            info_str += f"Action Group: {action_info['action_group']}\n"
                            info_str += f"Function: {action_info['function']}\n"
                            info_str += "Parameters:\n"
                            for param in action_info['parameters']:
                                info_str += f"  - {param['name']}: {param['value']}\n"
                            info_str += "==================\n"
                            eval_info.append(info_str)

                if "chunk" in event:
                    chunk_data = event["chunk"]["bytes"].decode("utf-8")
                    if chunk_data:  # Only append non-empty chunks
                        chunks.append(chunk_data)
                elif "content" in event:
                    content = event["content"]
                    if content:  # Only append non-empty content
                        chunks.append(content)
            except Exception as e:
                print(f"Error processing chunk: {e}")
                continue

        result = "".join(chunks)
        if not result.strip():
            raise ValueError("Empty response from Bedrock agent")

        if mode == "eval" and eval_info:
            return {"result": result, "eval_info": eval_info}
        else:
            return result

    except Exception as e:
        error_message = f"Error invoking Bedrock agent: {str(e)}"
        print(error_message)
        # Return a user-friendly error message
        return f"申し訳ありません。エラーが発生しました: {str(e)}"

@app.event("app_mention")
async def handle_app_mention(event, say):
    print("Received event:", event)
    user = event["user"]
    text = event["text"]
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event["ts"])

    # 対応中のメッセージをすぐに送信
    await say(
        text="Handling your request...",
        channel=channel,
        thread_ts=thread_ts
    )

    # bot のメンション部分を取り除く
    cleaned_text = text.split("<@", 1)[-1].split(">", 1)[-1].strip()

    # Bedrock Agent へ送信
    agent_response = invoke_bedrock_agent(cleaned_text)

    # Slack に返信（必ずスレッドに返信）
    response = await say(
        text=agent_response,
        channel=channel,
        thread_ts=thread_ts
    )
    
    try:
        # Add reactions to the response message
        await app.client.reactions_add(
            channel=channel,
            timestamp=response["ts"],
            name="thumbsup"
        )
        await app.client.reactions_add(
            channel=channel,
            timestamp=response["ts"],
            name="thumbsdown"
        )
    except Exception as e:
        print(f"Error adding reactions: {e}")

    try:
        current_call = weave.require_current_call()
        current_call.feedback.add("message_info", {
            "message_ts": response["ts"],
            "thread_ts": thread_ts,
            "channel": channel
        })
    except Exception as e:
        print(f"Error storing message info in weave: {e}")

@app.event("reaction_added")
async def handle_reaction(event):
    """Handle reaction added events."""
    if event["user"] != (await app.client.auth_test())["user_id"]:  # Ignore bot's own reactions
        item = event["item"]
        if item["type"] == "message":
            try:
                # Get conversation replies to verify the message
                conversation = await app.client.conversations_replies(
                    channel=item["channel"],
                    ts=item["ts"],
                    inclusive=True,
                    limit=1
                )
                messages = conversation.get("messages", [])
                if messages and len(messages):
                    thread_ts = messages[0].get("thread_ts")
                    if thread_ts:
                        weave_client = weave.init(os.environ["WANDB_ENTITY"] + "/" + os.environ["WANDB_PROJECT"])
                        all_calls = weave_client.get_calls()
                        for call in all_calls:
                            message_info = call.feedback.get("message_info", {})
                            if (message_info and 
                                message_info.get("message_ts") == item["ts"] and 
                                message_info.get("thread_ts") == thread_ts):
                                call.feedback.add_reaction(event["reaction"])
                                break
            except Exception as e:
                print(f"Error in reaction handling: {e}")

async def main():
    handler = AsyncSocketModeHandler(app, SLACK_APP_TOKEN)
    await handler.start_async()

if __name__ == "__main__":
    weave.init(os.environ["WANDB_ENTITY"] + "/" + os.environ["WANDB_PROJECT"])
    asyncio.run(main())
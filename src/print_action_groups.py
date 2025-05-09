import boto3
import json
import os

def list_agent_actions(agent_id, region_name='us-east-1'):
    """
    Amazon Bedrock Agentに登録されたアクションを取得して出力する関数
    
    Parameters:
    agent_id (str): エージェントのID
    region_name (str): AWSリージョン名（デフォルト: 'us-east-1'）
    
    Returns:
    dict: アクショングループとアクションの一覧
    """
    # Bedrock Agentのクライアントを作成
    bedrock_agent_client = boto3.client('bedrock-agent', region_name=region_name)
    
    # エージェントの最新バージョンを取得
    agent_response = bedrock_agent_client.get_agent(
        agentId=agent_id
    )
    # レスポンスの構造をデバッグ出力
    print("Agent Response:", json.dumps(agent_response, indent=2))
    agent_version = agent_response.get('agentStatus', {}).get('latestVersion', 'DRAFT')
    
    # エージェントのアクショングループを取得
    action_groups = []
    paginator = bedrock_agent_client.get_paginator('list_agent_action_groups')
    for page in paginator.paginate(agentId=agent_id, agentVersion=agent_version):
        action_groups.extend(page['agentActionGroupSummaries'])
    
    # 各アクショングループの詳細な情報を取得
    result = {}
    for action_group in action_groups:
        action_group_id = action_group['agentActionGroupId']
        
        # アクショングループの詳細を取得
        action_group_detail = bedrock_agent_client.get_agent_action_group(
            agentId=agent_id,
            agentActionGroupId=action_group_id,
            agentVersion=agent_version
        )
        
        # アクションスキーマの解析
        action_group_name = action_group_detail['agentActionGroupName']
        api_schema = json.loads(action_group_detail['apiSchema'])
        
        # OpenAPI形式のスキーマからアクションを抽出
        actions = []
        if 'paths' in api_schema:
            for path, methods in api_schema['paths'].items():
                for method, details in methods.items():
                    if 'operationId' in details:
                        action = {
                            'operationId': details['operationId'],
                            'path': path,
                            'method': method.upper(),
                            'description': details.get('description', ''),
                            'parameters': []
                        }
                        
                        # パラメータ情報の抽出
                        if 'parameters' in details:
                            for param in details['parameters']:
                                param_info = {
                                    'name': param['name'],
                                    'in': param['in'],
                                    'required': param.get('required', False),
                                    'type': param.get('schema', {}).get('type', 'unknown')
                                }
                                action['parameters'].append(param_info)
                        
                        actions.append(action)
        
        result[action_group_name] = actions
    
    return result

def print_agent_actions(agent_id, region_name='us-east-1'):
    """
    Amazon Bedrock Agentに登録されたアクションを取得して整形して出力する関数
    
    Parameters:
    agent_id (str): エージェントのID
    region_name (str): AWSリージョン名（デフォルト: 'us-east-1'）
    """
    try:
        # アクション一覧を取得
        action_groups = list_agent_actions(agent_id, region_name)
        
        # 結果の整形と出力
        print(f"Agent ID: {agent_id}\n")
        
        if not action_groups:
            print("アクショングループが見つかりませんでした。")
            return
        
        for group_name, actions in action_groups.items():
            print(f"===== アクショングループ: {group_name} =====")
            
            if not actions:
                print("  アクションが見つかりませんでした。")
                continue
            
            for i, action in enumerate(actions, 1):
                print(f"\nアクション {i}: {action['operationId']}")
                print(f"  パス: {action['path']}")
                print(f"  メソッド: {action['method']}")
                
                if action['description']:
                    print(f"  説明: {action['description']}")
                
                if action['parameters']:
                    print("  パラメータ:")
                    for param in action['parameters']:
                        required = "必須" if param['required'] else "任意"
                        print(f"    - {param['name']} ({param['in']}, {param['type']}, {required})")
                else:
                    print("  パラメータ: なし")
            
            print("\n")
    
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

# 使用例
if __name__ == "__main__":
    # エージェントIDを指定して実行
    agent_id = os.environ["AGENT_ID"]
    region_name = os.environ["AWS_REGION"] 
    
    print_agent_actions(agent_id, region_name)
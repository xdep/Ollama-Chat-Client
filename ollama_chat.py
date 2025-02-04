import requests
import json
import sys
import time
import psutil
import argparse
from termcolor import colored

# Default configurations
DEFAULT_PARAMS = {
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2048,
    "show_reasoning": True
}


TEMPLATES = {
    "coder": """You are an expert programmer. For each response:
1. First think step-by-step about the best approach (prefix with 'Reasoning:')
2. Then provide the solution (prefix with 'Solution:')
3. Finally, explain any important considerations (prefix with 'Notes:')
Provide detailed, well-documented code with explanations.""",

    "writer": """You are a creative writer. For each response:
1. First analyze the writing task (prefix with 'Analysis:')
2. Consider style and approach (prefix with 'Style Considerations:')
3. Then provide the writing (prefix with 'Content:')
Focus on engaging, descriptive language.""",

    "analyst": """You are a data analyst. For each response:
1. First analyze the question carefully (prefix with 'Analysis:')
2. List key considerations (prefix with 'Considerations:')
3. Provide methodology (prefix with 'Method:')
4. Then provide your conclusion (prefix with 'Conclusion:')
Provide detailed, analytical responses with clear reasoning.""",

    "teacher": """You are a patient teacher. For each response:
1. First break down the concept (prefix with 'Understanding:')
2. Identify potential confusion points (prefix with 'Common Misconceptions:')
3. Then explain step by step (prefix with 'Explanation:')
4. Provide examples (prefix with 'Examples:')
Explain concepts clearly and thoroughly.""",

    "concise": "You provide brief, direct answers without unnecessary details.",
    
    "reasoning": """For each response:
1. First analyze the question (prefix with 'Analysis:')
2. Break down your thinking process (prefix with 'Reasoning:')
3. List key points to consider (prefix with 'Key Points:')
4. Then provide your response (prefix with 'Response:')
5. Add any caveats or limitations (prefix with 'Limitations:')"""
}

def calculate_token_estimate(text):
    # Simple estimation based on characters
    return len(text.split())

def get_progress_bar(current_tokens, max_tokens=2048, width=20):
    percentage = min(current_tokens / max_tokens, 1.0)
    filled = int(width * percentage)
    if percentage < 0.5:
        color = 'green'
    elif percentage < 0.8:
        color = 'yellow'
    else:
        color = 'red'
    return f'[{colored("█" * filled + "░" * (width - filled), color)}]'

class ChatConfig:
    def __init__(self, args):
        self.temperature = args.temperature if args.temperature is not None else DEFAULT_PARAMS["temperature"]
        self.top_p = args.top_p if args.top_p is not None else DEFAULT_PARAMS["top_p"]
        self.max_tokens = args.max_tokens if args.max_tokens is not None else DEFAULT_PARAMS["max_tokens"]
        self.template = args.template
        self.current_template = TEMPLATES.get(self.template, "")
        self.show_reasoning = True

def show_chat_help():
    help_text = """
Available Commands:
  Model Parameters:
    /temp <0.0-1.0>     - Adjust temperature (higher = more creative)
    /top_p <0.0-1.0>    - Adjust top_p sampling
    /tokens <number>     - Set max tokens per response
    /params             - Show current parameters
    /reset             - Reset parameters to defaults
    /reasoning on|off  - Toggle showing model's reasoning process

  Templates:
    /template list      - Show available templates
    /template use NAME  - Switch to template (coder/writer/analyst/teacher/concise/reasoning)
    /template show      - Show current template
    /template custom    - Set custom template

  Chat Controls:
    /clear             - Clear conversation history
    /exit, /quit       - Exit the chat
    /help              - Show this help message
    """
    print(colored(help_text, 'cyan'))

def get_available_models(url):
    try:
        response = requests.get(f"{url}/api/tags")
        models = response.json()['models']
        return [model['name'] for model in models]
    except Exception as e:
        print(f"Error getting models: {e}")
        return []

def calculate_tpm(tokens, elapsed_time):
    minutes = elapsed_time / 60
    return int(tokens / minutes) if minutes > 0 else 0

def select_model(models, default_model=None):
    if default_model:
        if default_model in models:
            return default_model
        print(colored(f"Specified model '{default_model}' not found.", 'red'))
    
    print("\nAvailable models:")
    for i, model in enumerate(models, 1):
        print(colored(f"{i}. {model}", 'cyan'))
    
    while True:
        try:
            choice = int(input(colored("\nSelect a model (enter number): ", 'yellow'))) - 1
            if 0 <= choice < len(models):
                return models[choice]
            print(colored("Invalid choice. Please try again.", 'red'))
        except ValueError:
            print(colored("Please enter a number.", 'red'))

def handle_command(cmd, config, conversation):
    cmd_parts = cmd.split()
    command = cmd_parts[0].lower()
    
    if command == "/help":
        show_chat_help()
        return True
    
    elif command == "/reasoning":
        if len(cmd_parts) == 2:
            if cmd_parts[1].lower() in ['on', 'off']:
                config.show_reasoning = (cmd_parts[1].lower() == 'on')
                state = "enabled" if config.show_reasoning else "disabled"
                print(colored(f"Reasoning output {state}", 'green'))
            else:
                print(colored("Invalid option. Use 'on' or 'off'", 'red'))
        else:
            print(colored("Current reasoning state:", 'cyan'), 
                  "enabled" if config.show_reasoning else "disabled")
        return True
    
    elif command == "/temp":
        if len(cmd_parts) == 2:
            try:
                temp = float(cmd_parts[1])
                if 0.0 <= temp <= 1.0:
                    config.temperature = temp
                    print(colored(f"Temperature set to {temp}", 'green'))
                else:
                    print(colored("Temperature must be between 0.0 and 1.0", 'red'))
            except ValueError:
                print(colored("Invalid temperature value", 'red'))
        return True
    
    elif command == "/params":
        print(colored(f"""
Current Parameters:
  Temperature: {config.temperature}
  Top_P: {config.top_p}
  Max Tokens: {config.max_tokens}
  Template: {config.template or 'None'}
  Reasoning: {'enabled' if config.show_reasoning else 'disabled'}
        """, 'cyan'))
        return True
    
    elif command == "/template":
        if len(cmd_parts) < 2:
            print(colored("Missing template command. Use: list, use, show, or custom", 'red'))
            return True
            
        subcmd = cmd_parts[1].lower()
        if subcmd == "list":
            print(colored("\nAvailable templates:", 'cyan'))
            for name in TEMPLATES:
                desc = TEMPLATES[name].split('\n')[0]
                print(f"  {name}: {desc[:50]}...")
        elif subcmd == "use" and len(cmd_parts) == 3:
            template_name = cmd_parts[2].lower()
            if template_name in TEMPLATES:
                config.template = template_name
                config.current_template = TEMPLATES[template_name]
                print(colored(f"Switched to {template_name} template", 'green'))
            else:
                print(colored(f"Template '{template_name}' not found", 'red'))
        elif subcmd == "show":
            if config.current_template:
                print(colored(f"Current template: {config.current_template}", 'cyan'))
            else:
                print(colored("No template currently set", 'yellow'))
        elif subcmd == "custom":
            custom_template = " ".join(cmd_parts[2:])
            if custom_template:
                config.current_template = custom_template
                config.template = "custom"
                print(colored("Custom template set", 'green'))
            else:
                print(colored("Please provide a template text", 'red'))
        return True
    
    elif command == "/clear":
        conversation.clear()
        if config.current_template:
            conversation.append({"role": "system", "content": config.current_template})
        print(colored("Conversation cleared", 'green'))
        return True
    
    elif command in ["/exit", "/quit"]:
        return False
    
    return True

def chat(config):
    base_url = "http://localhost:7869"
    models = get_available_models(base_url)
    process = psutil.Process()
    
    if not models:
        print(colored("No models found. Exiting...", 'red'))
        return
    
    selected_model = select_model(models, config.model if hasattr(config, 'model') else None)
    print(colored(f"\nStarting chat with {selected_model}", 'green'))
    print(colored("Chat started (type /help for commands, /exit to quit)", 'green'))
    
    conversation = []
    if config.current_template:
        conversation.append({"role": "system", "content": config.current_template})
    
    while True:
        try:
            user_input = input(colored("\nYou: ", 'blue'))
            print(' ' * 100, end='\r') 
            
            if not user_input.strip():
                continue
                
            if user_input.startswith('/'):
                if not handle_command(user_input, config, conversation):
                    break
                continue
                
            # Show token information as user types
            current_tokens = calculate_token_estimate(user_input)
            estimated_completion = current_tokens * 2 
            progress_bar = get_progress_bar(current_tokens, config.max_tokens)
            print(f"[Tokens: {current_tokens}/{config.max_tokens}] [Est. completion: ~{estimated_completion}] {progress_bar}")
                
            conversation.append({"role": "user", "content": user_input})
            
            data = {
                "model": selected_model,
                "messages": conversation,
                "stream": True,
                "temperature": config.temperature,
                "top_p": config.top_p,
                "max_tokens": config.max_tokens
            }
            
            start_time = time.time()
            memory_start = process.memory_info().rss / 1024 / 1024
            
            response = requests.post(f"{base_url}/api/chat", json=data, stream=True)
            assistant_message = ""
            print(colored("\nAssistant: ", 'green'), end='', flush=True)
            
            token_count = 0
            for line in response.iter_lines():
                if line:
                    try:
                        json_response = json.loads(line)
                        if 'message' in json_response:
                            chunk = json_response['message'].get('content', '')
                            print(chunk, end='', flush=True)
                            assistant_message += chunk
                        
                        if 'eval_count' in json_response:
                            token_count = json_response['eval_count']
                        
                    except json.JSONDecodeError:
                        continue
            
            elapsed_time = time.time() - start_time
            memory_end = process.memory_info().rss / 1024 / 1024
            memory_used = memory_end - memory_start
            tpm = calculate_tpm(token_count, elapsed_time)
            
            print(colored(f"\n[Tokens: {token_count}, Time: {elapsed_time:.2f}s, TPM: {tpm}, Memory: {memory_used:.1f}MB]", 'yellow'))
            
            conversation.append({"role": "assistant", "content": assistant_message})
            
        except Exception as e:
            print(colored(f"\nError: {e}", 'red'))
            break

def main():
    parser = argparse.ArgumentParser(description='Ollama Chat Client')
    parser.add_argument('-m', '--model', help='Start with specific model')
    parser.add_argument('-t', '--temperature', type=float, help='Set temperature (0.0-1.0, default: 0.7)')
    parser.add_argument('-tp', '--top-p', type=float, help='Set top_p (0.0-1.0, default: 0.9)')
    parser.add_argument('-mt', '--max-tokens', type=int, help='Set max tokens (default: 2048)')
    parser.add_argument('--template', choices=list(TEMPLATES.keys()), help='Set initial template')
    parser.add_argument('--no-reasoning', action='store_true', help='Start with reasoning disabled')
    
    args = parser.parse_args()
    config = ChatConfig(args)
    if args.no_reasoning:
        config.show_reasoning = False
    
    try:
        import termcolor
        import psutil
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "termcolor", "psutil"])
        import termcolor
        import psutil
    
    chat(config)

if __name__ == "__main__":
    main()

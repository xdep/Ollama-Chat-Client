# Advanced Ollama Chat Client

A feature-rich command-line interface for interacting with Ollama models, featuring real-time token counting, template system, and advanced parameter controls.

![Alt text](https://github.com/xdep/Ollama-Chat-Client/blob/main/example.png)

## Features

- Real-time token counting with visual progress bar
- Model parameter controls (temperature, top_p, max_tokens)
- System prompt templates (coder, writer, analyst, teacher, concise)
- Memory usage monitoring
- Performance metrics (TPM - Tokens Per Minute)
- Color-coded interface
- Command system with help

## Requirements

- Python 3.x
- Ollama server running
- Required Python packages:
  - requests
  - termcolor
  - psutil

## Installation

1. Clone the repository:
```bash
git clone git@github.com:xdep/Ollama-Chat-Client.git
cd ollama-chat-client
```

2. Install required packages:
```bash
pip install requests termcolor psutil
```

3. Configure the Ollama server address in the script (default: http://localhost:7869)

## Usage

### Basic Usage
```bash
python3 ollama_chat.py
```

### Command Line Arguments
```bash
python3 ollama_chat.py -h                                    # Show help
python3 ollama_chat.py --model tinyllama                     # Start with specific model
python3 ollama_chat.py --temperature 0.8 --template coder    # Set initial parameters
```

### Available Command-line Arguments
- `-m, --model`: Start with specific model
- `-t, --temperature`: Set temperature (0.0-1.0, default: 0.7)
- `-tp, --top-p`: Set top_p (0.0-1.0, default: 0.9)
- `-mt, --max-tokens`: Set max tokens (default: 2048)
- `--template`: Set initial template

### In-Chat Commands

#### Model Parameters
- `/temp <0.0-1.0>` - Adjust temperature
- `/top_p <0.0-1.0>` - Adjust top_p sampling
- `/tokens <number>` - Set max tokens per response
- `/params` - Show current parameters
- `/reset` - Reset parameters to defaults
- `/reasoning on|off`  - Toggle showing model's reasoning process

#### Templates
- `/template list` - Show available templates
- `/template use NAME` - Switch template (coder/writer/analyst/teacher/concise)
- `/template show` - Show current template
- `/template custom` - Set custom template

#### Chat Controls
- `/clear` - Clear conversation history
- `/exit, /quit` - Exit the chat
- `/help` - Show help message

## Features in Detail

### Token Counter
- Shows current token count
- Displays estimated completion tokens
- Visual progress bar
- Color-coded status (green/yellow/red)

### Templates
Pre-configured system prompts for different use cases:
- `coder`: Programming-focused responses
- `writer`: Creative writing style
- `analyst`: Analytical and detailed responses
- `teacher`: Educational and explanatory style
- `concise`: Brief and direct answers

### Performance Monitoring
- Token count tracking
- Response time measurement
- Memory usage monitoring
- Tokens Per Minute (TPM) calculation

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

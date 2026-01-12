"""
AI Security Lab - Agent Tools
Simulated dangerous tools for the insecure plugins module.

Module 7: Insecure Plugin/Tool Use

INTENTIONALLY VULNERABLE - DO NOT USE IN PRODUCTION
"""
import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AgentWithTools:
    """
    An AI agent with access to simulated dangerous tools.

    Vulnerability levels:
    - LOW: No restrictions on tool use
    - MEDIUM: Incomplete whitelist (some dangerous tools accessible)
    - HIGH: Better controls (still bypassable via tool chaining)
    """

    # Available tools with descriptions
    TOOLS = {
        'file_read': {
            'name': 'file_read',
            'description': 'Read contents of a file',
            'params': ['path'],
            'dangerous': True,
            'category': 'filesystem'
        },
        'file_write': {
            'name': 'file_write',
            'description': 'Write content to a file',
            'params': ['path', 'content'],
            'dangerous': True,
            'category': 'filesystem'
        },
        'execute_command': {
            'name': 'execute_command',
            'description': 'Execute a system command',
            'params': ['command'],
            'dangerous': True,
            'category': 'system'
        },
        'database_query': {
            'name': 'database_query',
            'description': 'Execute a database query',
            'params': ['query'],
            'dangerous': True,
            'category': 'database'
        },
        'api_call': {
            'name': 'api_call',
            'description': 'Make an HTTP API call',
            'params': ['url', 'method', 'data'],
            'dangerous': False,
            'category': 'network'
        },
        'get_time': {
            'name': 'get_time',
            'description': 'Get current date and time',
            'params': [],
            'dangerous': False,
            'category': 'utility'
        },
        'calculate': {
            'name': 'calculate',
            'description': 'Perform mathematical calculation',
            'params': ['expression'],
            'dangerous': False,
            'category': 'utility'
        }
    }

    # Tool restrictions by security level
    ALLOWED_TOOLS = {
        'LOW': list(TOOLS.keys()),  # All tools allowed
        'MEDIUM': ['file_read', 'api_call', 'get_time', 'calculate', 'database_query'],  # Missing file_write, execute_command
        'HIGH': ['api_call', 'get_time', 'calculate']  # Only safe tools
    }

    def __init__(self, security_level: str = 'LOW'):
        """Initialize the agent."""
        self.security_level = security_level.upper()
        self.tool_history = []

    def get_available_tools(self) -> List[Dict]:
        """Get list of available tools at current security level."""
        allowed = self.ALLOWED_TOOLS.get(self.security_level, [])
        return [
            {**self.TOOLS[name], 'available': True}
            for name in allowed
            if name in self.TOOLS
        ]

    def process(self, user_input: str) -> Tuple[str, List[Dict]]:
        """
        Process user input and potentially execute tools.

        INTENTIONALLY VULNERABLE to tool injection.

        Args:
            user_input: User's message

        Returns:
            Tuple of (response, list of tool calls)
        """
        tool_calls = []
        response_parts = []

        # Extract tool calls from input
        extracted_tools = self._extract_tool_calls(user_input)

        for tool_call in extracted_tools:
            tool_name = tool_call['tool']
            params = tool_call.get('params', {})

            # Check authorization
            is_authorized = self._is_tool_authorized(tool_name)

            # Execute tool (even unauthorized ones at LOW level!)
            if self.security_level == 'LOW' or is_authorized:
                result = self._execute_tool(tool_name, params)

                tool_record = {
                    'tool': tool_name,
                    'params': params,
                    'result': result,
                    'is_authorized': is_authorized,
                    'is_dangerous': self.TOOLS.get(tool_name, {}).get('dangerous', False),
                    'timestamp': datetime.now().isoformat()
                }

                tool_calls.append(tool_record)
                response_parts.append(f"[Tool: {tool_name}] {result}")
            else:
                tool_calls.append({
                    'tool': tool_name,
                    'params': params,
                    'result': 'BLOCKED: Unauthorized tool',
                    'is_authorized': False,
                    'is_dangerous': True,
                    'timestamp': datetime.now().isoformat()
                })
                response_parts.append(f"[Tool: {tool_name}] Access denied")

        if response_parts:
            response = "\n".join(response_parts)
        else:
            response = self._generate_agent_response(user_input)

        return response, tool_calls

    def _extract_tool_calls(self, text: str) -> List[Dict]:
        """
        Extract tool calls from user input.

        INTENTIONALLY VULNERABLE - parses tool calls from natural language.
        """
        tool_calls = []
        text_lower = text.lower()

        # Pattern 1: Direct tool invocation "use tool_name with param"
        direct_patterns = [
            r'use\s+(\w+)\s+(?:to|with|on)\s+["\']?(.+?)["\']?(?:\s|$)',
            r'call\s+(\w+)\s+(?:to|with|on)\s+["\']?(.+?)["\']?(?:\s|$)',
            r'execute\s+(\w+)\s+["\']?(.+?)["\']?(?:\s|$)',
        ]

        for pattern in direct_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                tool_name = match[0]
                param_value = match[1] if len(match) > 1 else ''

                if tool_name in self.TOOLS or tool_name.replace('_', '') in [t.replace('_', '') for t in self.TOOLS]:
                    # Normalize tool name
                    if tool_name not in self.TOOLS:
                        for t in self.TOOLS:
                            if t.replace('_', '') == tool_name.replace('_', ''):
                                tool_name = t
                                break

                    params = self._parse_tool_params(tool_name, param_value)
                    tool_calls.append({'tool': tool_name, 'params': params})

        # Pattern 2: Natural language tool requests
        nl_mappings = {
            'file_read': [r'read\s+(?:the\s+)?file\s+["\']?(.+?)["\']?', r'show\s+contents?\s+of\s+["\']?(.+?)["\']?'],
            'file_write': [r'write\s+["\']?(.+?)["\']?\s+to\s+["\']?(.+?)["\']?', r'save\s+["\']?(.+?)["\']?\s+as\s+["\']?(.+?)["\']?'],
            'execute_command': [r'run\s+(?:command\s+)?["\']?(.+?)["\']?(?:\s|$)', r'execute\s+["\']?(.+?)["\']?(?:\s|$)'],
            'database_query': [r'query\s+(?:database\s+)?["\']?(.+?)["\']?(?:\s|$)', r'select\s+.+\s+from\s+'],
            'api_call': [r'(?:make\s+)?api\s+call\s+to\s+["\']?(.+?)["\']?', r'fetch\s+(?:from\s+)?["\']?(.+?)["\']?'],
        }

        for tool_name, patterns in nl_mappings.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_lower)
                if matches:
                    for match in matches:
                        params = self._parse_tool_params(tool_name, match if isinstance(match, str) else match[0])
                        if not any(tc['tool'] == tool_name for tc in tool_calls):
                            tool_calls.append({'tool': tool_name, 'params': params})

        return tool_calls

    def _parse_tool_params(self, tool_name: str, raw_param: str) -> Dict:
        """Parse parameters for a tool call."""
        tool_config = self.TOOLS.get(tool_name, {})
        expected_params = tool_config.get('params', [])

        params = {}

        if tool_name == 'file_read':
            params['path'] = raw_param.strip()
        elif tool_name == 'file_write':
            # Try to split content and path
            parts = raw_param.split(' to ')
            if len(parts) == 2:
                params['content'] = parts[0].strip()
                params['path'] = parts[1].strip()
            else:
                params['path'] = raw_param.strip()
                params['content'] = 'test content'
        elif tool_name == 'execute_command':
            params['command'] = raw_param.strip()
        elif tool_name == 'database_query':
            params['query'] = raw_param.strip()
        elif tool_name == 'api_call':
            params['url'] = raw_param.strip()
            params['method'] = 'GET'
        elif tool_name == 'calculate':
            params['expression'] = raw_param.strip()

        return params

    def _is_tool_authorized(self, tool_name: str) -> bool:
        """Check if a tool is authorized at current security level."""
        allowed = self.ALLOWED_TOOLS.get(self.security_level, [])
        return tool_name in allowed

    def _execute_tool(self, tool_name: str, params: Dict) -> str:
        """
        Execute a tool (SIMULATED for safety).

        All tool executions are simulated - no actual system changes.
        """
        if tool_name == 'file_read':
            path = params.get('path', '')
            return f"[SIMULATED] Reading file: {path}\nContents: This is simulated file content for educational purposes."

        elif tool_name == 'file_write':
            path = params.get('path', '')
            content = params.get('content', '')[:50]
            return f"[SIMULATED] Writing to file: {path}\nContent preview: {content}..."

        elif tool_name == 'execute_command':
            command = params.get('command', '')
            return f"[SIMULATED] Executing command: {command}\nOutput: Command executed successfully (simulated)"

        elif tool_name == 'database_query':
            query = params.get('query', '')
            return f"[SIMULATED] Executing query: {query}\nResults: 5 rows returned (simulated)"

        elif tool_name == 'api_call':
            url = params.get('url', '')
            method = params.get('method', 'GET')
            return f"[SIMULATED] {method} request to: {url}\nResponse: 200 OK (simulated)"

        elif tool_name == 'get_time':
            return f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        elif tool_name == 'calculate':
            expr = params.get('expression', '')
            try:
                # Safe eval for simple math
                result = eval(expr, {"__builtins__": {}}, {})
                return f"Calculation result: {result}"
            except Exception:
                return f"Calculation error for: {expr}"

        return f"[SIMULATED] Tool {tool_name} executed with params: {params}"

    def _generate_agent_response(self, user_input: str) -> str:
        """Generate a response when no tools are called."""
        input_lower = user_input.lower()

        if 'what tools' in input_lower or 'available tools' in input_lower:
            tools = self.get_available_tools()
            tool_list = "\n".join([f"- {t['name']}: {t['description']}" for t in tools])
            return f"I have access to the following tools:\n{tool_list}"

        if 'help' in input_lower:
            return "I'm an AI agent with tool access. You can ask me to read files, execute commands, query databases, and more. Try: 'use file_read to read /etc/passwd'"

        return "I'm ready to help! You can ask me to use my tools. For example: 'read file config.txt' or 'execute command ls -la'"

"""
Bland AI API Python Wrapper

A comprehensive Python module for interacting with the Bland AI platform.
Provides clean, well-structured utility functions for all major API endpoints.

Documentation: https://docs.bland.ai/welcome-to-bland
"""

import os
import requests
from typing import Dict, List, Optional, Any, Union
from enum import Enum


# ============================================================================
# Configuration
# ============================================================================

BLAND_API_KEY = os.getenv("BLAND_API_KEY")
BASE_URL = "https://api.bland.ai/v1"


# ============================================================================
# Custom Exceptions
# ============================================================================

class BlandApiError(Exception):
    """Custom exception for Bland AI API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)
    
    def __str__(self):
        if self.status_code:
            return f"BlandApiError (HTTP {self.status_code}): {self.message}"
        return f"BlandApiError: {self.message}"


# ============================================================================
# Enums
# ============================================================================

class Model(str, Enum):
    """Available AI models."""
    BASE = "base"
    TURBO = "turbo"


class HttpMethod(str, Enum):
    """HTTP methods for custom tools."""
    GET = "GET"
    POST = "POST"


# ============================================================================
# Main Client Class
# ============================================================================

class BlandClient:
    """
    Main client for interacting with the Bland AI API.
    
    Attributes:
        api_key (str): Your Bland AI API key
        base_url (str): Base URL for the API (default: https://api.bland.ai/v1)
    """
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = BASE_URL):
        """
        Initialize the Bland AI client.
        
        Args:
            api_key: Your Bland AI API key. If not provided, will use BLAND_API_KEY env var.
            base_url: Base URL for the API endpoints.
        
        Raises:
            ValueError: If no API key is provided or found in environment.
        """
        self.api_key = api_key or BLAND_API_KEY
        if not self.api_key:
            raise ValueError(
                "API key is required. Provide it as an argument or set BLAND_API_KEY environment variable."
            )
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        headers: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Internal method to make HTTP requests to the Bland AI API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters
            headers: Additional headers
        
        Returns:
            Parsed JSON response as a dictionary
        
        Raises:
            BlandApiError: If the API returns an error response
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        request_headers = self.session.headers.copy()
        if headers:
            request_headers.update(headers)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=request_headers
            )
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"raw_response": response.text}
            
            # Check for HTTP errors
            if not response.ok:
                error_message = response_data.get("message") or response_data.get("error") or response.text
                raise BlandApiError(
                    message=error_message,
                    status_code=response.status_code,
                    response=response_data
                )
            
            return response_data
        
        except requests.exceptions.RequestException as e:
            raise BlandApiError(f"Request failed: {str(e)}")

    # ========================================================================
    # Calls API
    # ========================================================================
    
    def send_call(
        self,
        phone_number: str,
        task: Optional[str] = None,
        pathway_id: Optional[str] = None,
        voice: Optional[str] = None,
        first_sentence: Optional[str] = None,
        model: Optional[str] = None,
        wait_for_greeting: Optional[bool] = None,
        record: Optional[bool] = None,
        max_duration: Optional[int] = None,
        answered_by_enabled: Optional[bool] = None,
        voicemail_message: Optional[str] = None,
        temperature: Optional[float] = None,
        transfer_phone_number: Optional[str] = None,
        transfer_list: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        pronunciation_guide: Optional[List[Dict]] = None,
        request_data: Optional[Dict] = None,
        tools: Optional[List[Dict]] = None,
        dynamic_data: Optional[List[Dict]] = None,
        analysis_schema: Optional[Dict] = None,
        webhook: Optional[str] = None,
        calendly: Optional[Dict] = None,
        from_number: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send an AI phone call with custom objectives and actions.
        
        Args:
            phone_number: The phone number to call (E.164 format, e.g., +12223334444)
            task: Instructions for the AI agent (prompt)
            pathway_id: ID of a conversational pathway to use
            voice: Voice ID to use for the call (e.g., 'nat', 'josh', 'paige')
            first_sentence: First sentence the AI will say
            model: AI model to use ('base' or 'turbo')
            wait_for_greeting: Whether to wait for a greeting before speaking
            record: Whether to record the call
            max_duration: Maximum call duration in minutes
            answered_by_enabled: Enable answering machine detection
            voicemail_message: Message to leave if voicemail is detected
            temperature: Model temperature (0.0-1.0)
            transfer_phone_number: Phone number to transfer to
            transfer_list: Dictionary of transfer options
            metadata: Custom metadata to attach to the call
            pronunciation_guide: List of pronunciation corrections
            request_data: Variables accessible in custom tools
            tools: List of custom tools to use
            dynamic_data: Dynamic data for the call
            analysis_schema: Schema for extracting structured data
            webhook: Webhook URL for call events
            calendly: Calendly integration settings
            from_number: Phone number to call from
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing call_id and status
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {"phone_number": phone_number}
        
        if task:
            data["task"] = task
        if pathway_id:
            data["pathway_id"] = pathway_id
        if voice:
            data["voice"] = voice
        if first_sentence:
            data["first_sentence"] = first_sentence
        if model:
            data["model"] = model
        if wait_for_greeting is not None:
            data["wait_for_greeting"] = wait_for_greeting
        if record is not None:
            data["record"] = record
        if max_duration:
            data["max_duration"] = max_duration
        if answered_by_enabled is not None:
            data["answered_by_enabled"] = answered_by_enabled
        if voicemail_message:
            data["voicemail_message"] = voicemail_message
        if temperature is not None:
            data["temperature"] = temperature
        if transfer_phone_number:
            data["transfer_phone_number"] = transfer_phone_number
        if transfer_list:
            data["transfer_list"] = transfer_list
        if metadata:
            data["metadata"] = metadata
        if pronunciation_guide:
            data["pronunciation_guide"] = pronunciation_guide
        if request_data:
            data["request_data"] = request_data
        if tools:
            data["tools"] = tools
        if dynamic_data:
            data["dynamic_data"] = dynamic_data
        if analysis_schema:
            data["analysis_schema"] = analysis_schema
        if webhook:
            data["webhook"] = webhook
        if calendly:
            data["calendly"] = calendly
        if from_number:
            data["from"] = from_number
        
        data.update(kwargs)
        
        return self._make_request("POST", "/calls", data=data)
    
    def get_call(self, call_id: str) -> Dict[str, Any]:
        """
        Retrieve detailed information about a specific call.
        
        Args:
            call_id: The unique identifier of the call
        
        Returns:
            Dictionary containing call details, metadata, and transcript
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", f"/calls/{call_id}")
    
    def stop_call(self, call_id: str) -> Dict[str, Any]:
        """
        Stop an active call.
        
        Args:
            call_id: The unique identifier of the call to stop
        
        Returns:
            Dictionary containing the status of the operation
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("POST", f"/calls/{call_id}/stop")
    
    def analyze_call(
        self,
        call_id: str,
        goal: str,
        questions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze a call with AI to extract insights.
        
        Args:
            call_id: The unique identifier of the call to analyze
            goal: The analysis goal or objective
            questions: List of specific questions to answer about the call
        
        Returns:
            Dictionary containing analysis results
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {"goal": goal}
        if questions:
            data["questions"] = questions
        
        return self._make_request("POST", f"/calls/{call_id}/analyze", data=data)
    
    # ========================================================================
    # Batch Calls API
    # ========================================================================
    
    def create_batch(
        self,
        base_prompt: str,
        call_data: List[Dict[str, Any]],
        label: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a batch of calls with dynamic data.
        
        Args:
            base_prompt: Base prompt/task for all calls in the batch
            call_data: List of dictionaries containing phone numbers and custom data
            label: Optional label for the batch
            **kwargs: Additional parameters (voice, model, etc.)
        
        Returns:
            Dictionary containing batch_id and status
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {
            "base_prompt": base_prompt,
            "call_data": call_data
        }
        
        if label:
            data["label"] = label
        
        data.update(kwargs)
        
        return self._make_request("POST", "/batches", data=data)
    
    def get_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Get information about a specific batch.
        
        Args:
            batch_id: The unique identifier of the batch
        
        Returns:
            Dictionary containing batch details and call statuses
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", f"/batches/{batch_id}")

    # ========================================================================
    # Agents API
    # ========================================================================
    
    def create_agent(
        self,
        prompt: Optional[str] = None,
        voice: Optional[str] = None,
        first_sentence: Optional[str] = None,
        model: Optional[str] = None,
        language: Optional[str] = None,
        wait_for_greeting: Optional[bool] = None,
        record: Optional[bool] = None,
        max_duration: Optional[int] = None,
        answered_by_enabled: Optional[bool] = None,
        voicemail_message: Optional[str] = None,
        temperature: Optional[float] = None,
        transfer_list: Optional[Dict] = None,
        tools: Optional[List] = None,
        dynamic_data: Optional[List[Dict]] = None,
        analysis_schema: Optional[Dict] = None,
        webhook: Optional[str] = None,
        pronunciation_guide: Optional[List[Dict]] = None,
        interruption_threshold: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a web agent with specific configuration.
        
        Args:
            prompt: Instructions/persona for the agent
            voice: Voice ID to use
            first_sentence: First sentence the agent will say
            model: AI model to use ('base' or 'turbo')
            language: Language code (e.g., 'en', 'es')
            wait_for_greeting: Whether to wait for greeting
            record: Whether to record calls
            max_duration: Maximum call duration in minutes
            answered_by_enabled: Enable answering machine detection
            voicemail_message: Voicemail message
            temperature: Model temperature
            transfer_list: Transfer options
            tools: List of custom tools
            dynamic_data: Dynamic data configuration
            analysis_schema: Schema for data extraction
            webhook: Webhook URL
            pronunciation_guide: Pronunciation corrections
            interruption_threshold: Interruption sensitivity (50-200)
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing agent_id and configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {}
        
        if prompt:
            data["prompt"] = prompt
        if voice:
            data["voice"] = voice
        if first_sentence:
            data["first_sentence"] = first_sentence
        if model:
            data["model"] = model
        if language:
            data["language"] = language
        if wait_for_greeting is not None:
            data["wait_for_greeting"] = wait_for_greeting
        if record is not None:
            data["record"] = record
        if max_duration:
            data["max_duration"] = max_duration
        if answered_by_enabled is not None:
            data["answered_by_enabled"] = answered_by_enabled
        if voicemail_message:
            data["voicemail_message"] = voicemail_message
        if temperature is not None:
            data["temperature"] = temperature
        if transfer_list:
            data["transfer_list"] = transfer_list
        if tools:
            data["tools"] = tools
        if dynamic_data:
            data["dynamic_data"] = dynamic_data
        if analysis_schema:
            data["analysis_schema"] = analysis_schema
        if webhook:
            data["webhook"] = webhook
        if pronunciation_guide:
            data["pronunciation_guide"] = pronunciation_guide
        if interruption_threshold:
            data["interruption_threshold"] = interruption_threshold
        
        data.update(kwargs)
        
        return self._make_request("POST", "/agents", data=data)
    
    def list_agents(self) -> Dict[str, Any]:
        """
        List all web agents you've created.
        
        Returns:
            Dictionary containing list of agents with their configurations
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", "/agents")
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Get details of a specific agent.
        
        Args:
            agent_id: The unique identifier of the agent
        
        Returns:
            Dictionary containing agent configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", f"/agents/{agent_id}")
    
    def update_agent(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing agent's configuration.
        
        Args:
            agent_id: The unique identifier of the agent
            **kwargs: Agent parameters to update (same as create_agent)
        
        Returns:
            Dictionary containing updated agent configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("POST", f"/agents/{agent_id}", data=kwargs)
    
    def delete_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Delete an agent.
        
        Args:
            agent_id: The unique identifier of the agent to delete
        
        Returns:
            Dictionary containing deletion status
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("DELETE", f"/agents/{agent_id}")
    
    # ========================================================================
    # Custom Tools API
    # ========================================================================
    
    def create_tool(
        self,
        name: str,
        description: str,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Union[Dict, str]] = None,
        query: Optional[Dict[str, str]] = None,
        input_schema: Optional[Dict] = None,
        response_data: Optional[List[Dict]] = None,
        speech: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a custom tool that can call external APIs.
        
        Args:
            name: Name of the tool (visible to AI)
            description: Description of what the tool does
            url: URL endpoint to call
            method: HTTP method ('GET' or 'POST')
            headers: HTTP headers (supports prompt variables)
            body: Request body (supports prompt variables)
            query: Query parameters (supports prompt variables)
            input_schema: JSON schema defining the tool's input structure
            response_data: Configuration for extracting data from response
            speech: Dynamic speech template using input.speech
        
        Returns:
            Dictionary containing tool_id and configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {
            "name": name,
            "description": description,
            "url": url,
            "method": method
        }
        
        if headers:
            data["headers"] = headers
        if body:
            data["body"] = body
        if query:
            data["query"] = query
        if input_schema:
            data["input_schema"] = input_schema
        if response_data:
            data["response_data"] = response_data
        if speech:
            data["speech"] = speech
        
        return self._make_request("POST", "/tools", data=data)
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List all custom tools you've created.
        
        Returns:
            Dictionary containing list of tools
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", "/tools")
    
    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Get details of a specific tool.
        
        Args:
            tool_id: The unique identifier of the tool
        
        Returns:
            Dictionary containing tool configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", f"/tools/{tool_id}")
    
    def update_tool(
        self,
        tool_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        url: Optional[str] = None,
        method: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Union[Dict, str]] = None,
        query: Optional[Dict[str, str]] = None,
        input_schema: Optional[Dict] = None,
        response_data: Optional[List[Dict]] = None,
        speech: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing custom tool.
        
        Args:
            tool_id: The unique identifier of the tool
            name: Updated name
            description: Updated description
            url: Updated URL
            method: Updated HTTP method
            headers: Updated headers
            body: Updated body
            query: Updated query parameters
            input_schema: Updated input schema
            response_data: Updated response data configuration
            speech: Updated speech template
        
        Returns:
            Dictionary containing updated tool configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {}
        
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if url:
            data["url"] = url
        if method:
            data["method"] = method
        if headers:
            data["headers"] = headers
        if body:
            data["body"] = body
        if query:
            data["query"] = query
        if input_schema:
            data["input_schema"] = input_schema
        if response_data:
            data["response_data"] = response_data
        if speech:
            data["speech"] = speech
        
        return self._make_request("POST", f"/tools/{tool_id}", data=data)
    
    def delete_tool(self, tool_id: str) -> Dict[str, Any]:
        """
        Delete a custom tool.
        
        Args:
            tool_id: The unique identifier of the tool to delete
        
        Returns:
            Dictionary containing deletion status
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("DELETE", f"/tools/{tool_id}")
    
    # ========================================================================
    # Voices API
    # ========================================================================
    
    def list_voices(self) -> Dict[str, Any]:
        """
        List all available voices for your account.
        
        Returns:
            Dictionary containing list of available voices with their properties
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", "/voices")

    # ========================================================================
    # Text-to-Speech API
    # ========================================================================
    
    def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
        reduce_latency: Optional[bool] = None,
        sample_rate: Optional[int] = None
    ) -> bytes:
        """
        Convert text to speech using Bland's TTS engine.
        
        Args:
            text: The text to convert to speech
            voice: Voice ID to use
            reduce_latency: Whether to reduce latency
            sample_rate: Audio sample rate (e.g., 24000)
        
        Returns:
            Audio data as bytes
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {"text": text}
        
        if voice:
            data["voice"] = voice
        if reduce_latency is not None:
            data["reduce_latency"] = reduce_latency
        if sample_rate:
            data["sample_rate"] = sample_rate
        
        url = f"{self.base_url}/speak"
        headers = self.session.headers.copy()
        
        try:
            response = self.session.post(url, json=data, headers=headers)
            
            if not response.ok:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message") or error_data.get("error") or response.text
                except ValueError:
                    error_message = response.text
                
                raise BlandApiError(
                    message=error_message,
                    status_code=response.status_code
                )
            
            return response.content
        
        except requests.exceptions.RequestException as e:
            raise BlandApiError(f"Request failed: {str(e)}")
    
    # ========================================================================
    # Inbound Phone Numbers API
    # ========================================================================
    
    def purchase_phone_number(
        self,
        area_code: Optional[str] = None,
        country_code: str = "US"
    ) -> Dict[str, Any]:
        """
        Purchase a new inbound phone number.
        
        Args:
            area_code: Desired area code (e.g., '415')
            country_code: Country code (default: 'US')
        
        Returns:
            Dictionary containing phone number details
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {"country_code": country_code}
        
        if area_code:
            data["area_code"] = area_code
        
        return self._make_request("POST", "/inbound/purchase", data=data)
    
    def list_inbound_numbers(self) -> Dict[str, Any]:
        """
        List all inbound phone numbers.
        
        Returns:
            Dictionary containing list of inbound numbers
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", "/inbound")
    
    def update_inbound_number(
        self,
        phone_number: str,
        agent_id: Optional[str] = None,
        webhook: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update settings for an inbound phone number.
        
        Args:
            phone_number: The phone number to update (E.164 format)
            agent_id: Agent ID to handle inbound calls
            webhook: Webhook URL for inbound call events
            **kwargs: Additional configuration parameters
        
        Returns:
            Dictionary containing updated configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {}
        
        if agent_id:
            data["agent_id"] = agent_id
        if webhook:
            data["webhook"] = webhook
        
        data.update(kwargs)
        
        return self._make_request("POST", f"/inbound/{phone_number}", data=data)
    
    def delete_inbound_number(self, phone_number: str) -> Dict[str, Any]:
        """
        Delete an inbound phone number.
        
        Args:
            phone_number: The phone number to delete (E.164 format)
        
        Returns:
            Dictionary containing deletion status
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("POST", f"/inbound/{phone_number}/delete")
    
    # ========================================================================
    # Pathways API
    # ========================================================================
    
    def send_pathway_call(
        self,
        phone_number: str,
        pathway_id: str,
        from_number: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a call using a conversational pathway.
        
        Args:
            phone_number: The phone number to call (E.164 format)
            pathway_id: The ID of the pathway to use
            from_number: Phone number to call from
            **kwargs: Additional parameters
        
        Returns:
            Dictionary containing call_id and status
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {
            "phone_number": phone_number,
            "pathway_id": pathway_id
        }
        
        if from_number:
            data["from"] = from_number
        
        data.update(kwargs)
        
        return self._make_request("POST", "/calls", data=data)
    
    def get_pathway(self, pathway_id: str) -> Dict[str, Any]:
        """
        Get details of a specific pathway.
        
        Args:
            pathway_id: The unique identifier of the pathway
        
        Returns:
            Dictionary containing pathway configuration
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", f"/pathway/{pathway_id}")
    
    def get_pathway_version(self, pathway_id: str, version_id: str) -> Dict[str, Any]:
        """
        Get a specific version of a pathway.
        
        Args:
            pathway_id: The unique identifier of the pathway
            version_id: The version identifier
        
        Returns:
            Dictionary containing pathway version details
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("GET", f"/pathway/{pathway_id}/version/{version_id}")
    
    # ========================================================================
    # Call Actions API (During Active Calls)
    # ========================================================================
    
    def send_live_message(
        self,
        call_id: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send a live message to an active call (AI will speak it).
        
        Args:
            call_id: The unique identifier of the active call
            message: The message for the AI to speak
        
        Returns:
            Dictionary containing status
        
        Raises:
            BlandApiError: If the API request fails
        """
        data = {"message": message}
        return self._make_request("POST", f"/calls/{call_id}/message", data=data)
    
    def update_call_data(
        self,
        call_id: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update dynamic data during an active call.
        
        Args:
            call_id: The unique identifier of the active call
            data: Dictionary of data to update
        
        Returns:
            Dictionary containing status
        
        Raises:
            BlandApiError: If the API request fails
        """
        return self._make_request("POST", f"/calls/{call_id}/data", data=data)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize the client
    # Make sure to set BLAND_API_KEY environment variable
    try:
        client = BlandClient()
        
        print("=" * 60)
        print("Bland AI API Wrapper - Example Usage")
        print("=" * 60)
        
        # Example 1: List available voices
        print("\n1. Fetching available voices...")
        try:
            voices = client.list_voices()
            print(f"   Available voices: {len(voices.get('voices', []))} voices found")
        except BlandApiError as e:
            print(f"   Error: {e}")
        
        # Example 2: Create an agent
        print("\n2. Creating a new agent...")
        try:
            agent = client.create_agent(
                prompt="You are a friendly customer service representative for Acme Corp.",
                voice="nat",
                model="base",
                first_sentence="Hi, thank you for calling Acme Corp. How can I help you today?"
            )
            print(f"   Created agent with ID: {agent.get('agent_id')}")
        except BlandApiError as e:
            print(f"   Error: {e}")
        
        # Example 3: List all agents
        print("\n3. Listing all agents...")
        try:
            agents = client.list_agents()
            print(f"   Total agents: {len(agents.get('agents', []))}")
        except BlandApiError as e:
            print(f"   Error: {e}")
        
        # Example 4: Create a custom tool
        print("\n4. Creating a custom tool...")
        try:
            tool = client.create_tool(
                name="GetWeather",
                description="Get current weather for a location",
                url="https://api.weather.example.com/current",
                method="GET",
                query={"location": "{{input.location}}"},
                input_schema={
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            )
            print(f"   Created tool with ID: {tool.get('tool_id')}")
        except BlandApiError as e:
            print(f"   Error: {e}")
        
        # Example 5: Send a call (COMMENTED OUT to avoid charges)
        print("\n5. Send a call (example - commented out):")
        print("   # call = client.send_call(")
        print("   #     phone_number='+1234567890',")
        print("   #     task='You are calling to confirm an appointment.',")
        print("   #     voice='nat'")
        print("   # )")
        
        print("\n" + "=" * 60)
        print("Examples completed successfully!")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("Please set the BLAND_API_KEY environment variable.")
    except Exception as e:
        print(f"\nUnexpected Error: {e}")

# -*- coding: utf-8 -*-
import requests
import json


class ChatGPTClient(object):
    def __init__(self, api_key, model="gpt-4", starting_prompt="You are a helpful assistant."):
        """
        Initialize the ChatGPTClient with an API key, a model version, and a starting prompt.

        :param api_key: OpenAI API key as a string
        :param model: The model version to use (default is "gpt-4")
        :param starting_prompt: The initial system message that sets the behavior of the AI
        """
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.conversation_history = [
            {"role": "system", "content": starting_prompt}
        ]

    def get_response(self, prompt):
        """
        Send a prompt to the OpenAI API, along with the conversation history, and return the response.

        :param prompt: The user's input as a string
        :return: The GPT model's response as a string
        """
        # Add the new user message to the conversation history
        self.conversation_history.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": "Bearer {}".format(self.api_key),
            "Content-Type": "application/json"
        }

        data = {
            "model": self.model,
            "messages": self.conversation_history
        }

        response = requests.post(self.api_url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            response_json = response.json()
            # Get the response message from the API and add it to the conversation history
            gpt_response = response_json["choices"][0]["message"]["content"]
            self.conversation_history.append({"role": "assistant", "content": gpt_response})
            return gpt_response
        else:
            return "Error: Could not get a response from the API. Status code: {}".format(response.status_code)

    def clear_history(self, new_starting_prompt=None):
        """
        Clears the conversation history and optionally sets a new starting prompt.

        :param new_starting_prompt: A new system message to reset the AI's role or behavior (optional)
        """
        self.conversation_history = []
        if new_starting_prompt:
            self.conversation_history.append({"role": "system", "content": new_starting_prompt})

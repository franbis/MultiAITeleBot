from abc import ABC, abstractmethod

from openai import OpenAI

from ai.schemas import Translation
from file_managers.config import ConfigurationManager



class AIManager(ABC):
	"""Abstract AI API manager. Reads API call options from a
	configuration file."""


	def __init__(self, options_path):
		self.options = ConfigurationManager(options_path)
	

	def check_for_visual_content(self, messages):
		"""Return True if a list of messages contains at least one
		message of which content type is set to 'image_url'."""
		for msg in messages:
			if isinstance(msg.content, list):
				for item in msg.content:
					if item['type'] == 'image_url':
						return True
		
		return False
	

	def get_preferred_model_settings(self, messages):
		"""Return a tuple with either the vision or the chat model
		based on if there's any visual content in a list of messages,
		and the max_tokens."""
		has_visual_ctx = self.check_for_visual_content(messages)
		model = self.options.get('vision.model') if has_visual_ctx else self.options.get('chat.model')
		max_tokens = self.options.get('vision.max_tokens') if has_visual_ctx else self.options.get('chat.max_tokens')
		
		return model, max_tokens
	

	def build_msg_content(self, texts=[], image_urls=[]):
		"""
		Build the content for a message.
		
		Args:
			texts:			Text list
			image_urls:		Image URL list
		"""

		content = []

		for text in texts:
			content.append({
				'type': 'text',
				'text': text,
			})
			
		for img_url in image_urls:
			content.append({
				'type': 'image_url',
				'image_url': {
					'url': img_url,
					**self.options.get('vision')
				},
			})
			
		return content


	@abstractmethod
	def chat(self, messages, **options):
		"""Call the LLM API and return the response."""
		pass


	@abstractmethod
	def translate(self, text, dst_lang='English', response_format=Translation, **options):
		"""Call the LLM API to translate a text and return the
		response."""
		pass


	@abstractmethod
	def tts(self, text, **options):
		"""Call the Text-to-Speech API and return the response."""
		pass


	@abstractmethod
	def stt(self, audio, **options):
		"""Call the Speech-to-Text API and return the response."""
		pass


	@abstractmethod
	def gen_imgs(self, prompt, **options):
		"""Call the image generation API and return the response."""
		pass


class OpenAIManager(AIManager):
	"""OpenAI API manager."""


	def __init__(self, api_key, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.client = OpenAI(api_key=api_key)


	def chat(self, messages, **options):
		return self.client.chat.completions.create(
			messages=messages,
			**(self.options.get('chat') | options)
		)
		
		
	def translate(self, text, dst_lang='English', response_format=Translation, **options):
		return self.client.beta.chat.completions.parse(
			messages=[
				{
					'role': 'system',
					'content': f'Translate the prompt to "{dst_lang}".',
				},
				{
					'role': 'user',
					'content': text,
				}
			],
			response_format=response_format,
			**(self.options.get('translation') | options)
		)

		
	def tts(self, text, **options):
		return self.client.audio.speech.create(
			input=text,
			**(self.options.get('tts') | options)
		)


	def stt(self, audio, **options):
		return self.client.audio.transcriptions.create(
			file=audio,
			**(self.options.get('stt') | options)
		)
	

	def gen_imgs(self, prompt, **options):
		return self.client.images.generate(
			prompt=prompt,
			**(self.options.get('image') | options)
		)
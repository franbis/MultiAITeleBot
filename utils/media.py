import io
from base64 import b64encode

import filetype

from PIL import Image

from pydub import AudioSegment



def strip_exif_data(img):
	"""Strip EXIF data from a PIL Image and return it."""
	data = list(img.getdata())
	img_wo_exif = Image.new(img.mode, img.size)
	img_wo_exif.putdata(data)
	return img_wo_exif
	

def speed_up_audio(audio_bytes, speed=2.0, chunk_size=50, crossfade=25):
	"""Speed-up an audio wave and return it."""
	audio_io = io.BytesIO(audio_bytes)

	# Guess the audio wave format.
	audio_type = filetype.guess(audio_bytes)
	audio_fmt = audio_type.extension if audio_type else None
	if audio_fmt:
		audio = AudioSegment.from_file(audio_io, format=audio_fmt)
		
		sped_up_audio = audio.speedup(
			playback_speed=speed,
			chunk_size=chunk_size,
			crossfade=crossfade
		)
	
		# Simulate a voice message recorded using Telegram (OGG).
		new_audio_bytes_io = io.BytesIO()
		sped_up_audio.export(new_audio_bytes_io, format="ogg")

	else:
		# The format could not be guessed, leave the wave as-is.
		new_audio_bytes_io = audio_io
	
	return new_audio_bytes_io.getvalue()


def create_image_url(img_bytes):
	"""Build the data-URL for an image."""
	
	# img_bytes could be used directly to construct the data-URL but it's
	# a good idea to first strip the exif data for security reasons.
	img = Image.open(io.BytesIO(img_bytes))
	new_img_bytesio = io.BytesIO()
	
	img_wo_exif = strip_exif_data(img)
	
	# Save as PNG to preserve details.
	img_wo_exif.save(new_img_bytesio, format='PNG')
	img_bytes = new_img_bytesio.getvalue()
	
	# It's probable that the content-type is always the same generic one.
	#content_type = requests.get(url).headers['Content-Type']
	# It may be that Telegram compresses pictures as JPEG.
	#content_type = 'image/jpeg'
	content_type = 'image/png'
	
	img.close()
	img_wo_exif.close()
	
	# NOTE: Do not add the "charset" parameter to the data-URL or ChatGPT
	#		won't be able to process the image.
	return f'data:{content_type};base64,{b64encode(img_bytes).decode()}'
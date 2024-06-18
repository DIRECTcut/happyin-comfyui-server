from comfy.api import queue_prompt
from comfy.utils import get_images, open_websocket_connection, save_image, track_progress


def generate_image_by_prompt(prompt, output_path, save_previews=False):
  try:
    ws, server_address, client_id = open_websocket_connection()
    prompt_id = queue_prompt(prompt, client_id, server_address)['prompt_id']
    track_progress(prompt, ws, prompt_id)
    images = get_images(prompt_id, server_address, save_previews)
    save_image(images, output_path, save_previews)
  finally:
    ws.close()
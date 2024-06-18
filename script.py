import websocket  # NOTE: websocket-client (https://github.com/websocket-client/websocket-client)
import uuid
import json
import urllib.request
import urllib.parse
import os
import urllib
from requests_toolbelt import MultipartEncoder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEVER_ADDRESS = "127.0.0.1:8188"
INSTRUCTIONS_DIR = 'workflows'
INSTRUCTIONS_FILE = 'gem.json'
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

UPLOADS_FOLDER = 'uploads'
UPLOAD_FILE = 'gem.png'

request_id = str(uuid.uuid4())

def queue_prompt(prompt):
    print(f'queueing prompt: {prompt}, client id: {request_id}')
    p = {"prompt": prompt, "request_id": request_id}
    data = json.dumps(p).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(SEVER_ADDRESS), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_image(filename, subfolder, folder_type):
    print(f'getting image: filename {filename}, subfolder {subfolder}')
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(SEVER_ADDRESS, url_values)) as response:
        return response.read()

def get_history(prompt_id):
    with urllib.request.urlopen("http://{}/history/{}".format(SEVER_ADDRESS, prompt_id)) as response:
        return json.loads(response.read())

def get_images(ws, prompt):
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break  # Execution is done
        else:
            continue  # Previews are binary data

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        if 'images' in node_output:
            images_output = []
            for image in node_output['images']:
                image_data = get_image(image['filename'], image['subfolder'], image['type'])
                images_output.append(image_data)
            output_images[node_id] = images_output

    return output_images

def save_images(images, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for node_id, image_list in images.items():
        for i, image_data in enumerate(image_list):
            image_path = os.path.join(output_dir, f"{node_id}_{i}.png")
            with open(image_path, 'wb') as img_file:
                img_file.write(image_data)
    print(f"Images saved to {output_dir}")

def upload_image(input_path, name, SEVER_ADDRESS, image_type="input", overwrite=False):
  with open(input_path, 'rb') as file:
    multipart_data = MultipartEncoder(
      fields= {
        'image': (name, file, 'image/png'),
        'type': image_type,
        'overwrite': str(overwrite).lower()
      }
    )

    data = multipart_data
    headers = { 'Content-Type': multipart_data.content_type }
    request = urllib.request.Request("http://{}/upload/image".format(SEVER_ADDRESS), data=data, headers=headers)
    with urllib.request.urlopen(request) as response:
      return response.read()

# Load the prompt from gem.json
path = os.path.join(BASE_DIR, INSTRUCTIONS_DIR, INSTRUCTIONS_FILE)
with open(path, 'r') as file:
    prompt_text = file.read()

image_path = os.path.join(BASE_DIR, UPLOADS_FOLDER, UPLOAD_FILE)
image_upload_as_filename = f"{request_id}-{UPLOAD_FILE}"
upload_image(image_path, image_upload_as_filename, SEVER_ADDRESS)

prompt = json.loads(prompt_text)
# input file filename
prompt["674"]["inputs"]["image"] = image_upload_as_filename

# resulting filenames
prompt["95"]["inputs"]["filename_prefix"] = f"{request_id}\\01"
prompt["399"]["inputs"]["filename_prefix"] = f"{request_id}\\02"
prompt["464"]["inputs"]["filename_prefix"] = f"{request_id}\\03"
prompt["482"]["inputs"]["filename_prefix"] = f"{request_id}\\04"
prompt["504"]["inputs"]["filename_prefix"] = f"{request_id}\\05"
prompt["521"]["inputs"]["filename_prefix"] = f"{request_id}\\06"

# Initialize WebSocket connection
# ws = websocket.create_connection("ws://{}/ws?clientId={}".format(SEVER_ADDRESS, request_id))

res = queue_prompt(prompt)
print(res)
# Get the images based on the prompt
# images = get_images(ws, prompt)

# Save the images to the output directory
# save_images(images, OUTPUT_DIR)

# Close the WebSocket connection
# ws.close()

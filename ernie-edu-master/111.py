import io

from PIL import Image
import base64
import json
image = Image.open(r"D:\python\pythonProject\ernie-edu-master\temp_images\8723e262-4e5a-436f-8a8f-1c31f97090f4_00001_.png")

with open(r"D:\python\pythonProject\ernie-edu-master\temp_images\8723e262-4e5a-436f-8a8f-1c31f97090f4_00001_.png", "rb") as image_file:
    image_data=image_file.read()

encodeed_image = base64.b64encode(image_data)

json_data={
    "image": encodeed_image.decode('utf-8')
}

json_data=json.dumps(json_data)
print(json_data)
wav = base64.b64decode(json_data.json()["wav"])
print(wav)


img = json_data['image'][0]
imagesa = Image.open(io.BytesIO(base64.b64decode(img.split("," ,1)[0])))
print(imagesa)
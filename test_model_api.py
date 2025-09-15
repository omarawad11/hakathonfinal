import requests

url = "https://tuvcontrol.horizonaii.com/face-recognition"

data = {
    "name": "Christian Bale"
}

files = {
    "image": open(r"C:\Users\aashq\Desktop\FR py\FRDS2\Rami Malek\Rami Malek23_3824.jpg", "rb")
}

response = requests.post(url, data=data, files=files)

print(response.json())

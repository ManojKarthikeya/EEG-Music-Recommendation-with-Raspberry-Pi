import requests

print(requests.post("https://a61c-49-43-229-15.ngrok-free.app/classify-brain-waves",
              json={"brainwaves": [[1, 2, 3, 4, 5, 6, 7, 8, 10, 11]]}))

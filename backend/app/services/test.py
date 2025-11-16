import requests
import json

def test_api():
    url = "http://localhost:8000/api/detect/all"
    
    # Замените путь на реальный путь к вашему тестовому изображению
    with open("test_image.jpg", "rb") as f:
        files = {"file": ("test.jpg", f, "image/jpeg")}
        response = requests.post(url, files=files)
    
    print("Status Code:", response.status_code)
    print("Response:", json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_api()
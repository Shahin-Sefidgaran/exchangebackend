import requests

headers = {
    'accept': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyN0BleGFtcGxlLmNvbSIsImV4cCI6MTYzMTI3MjkzOS4zNzk3NTJ9.Z1cB4OPb3hktVe1azlvXAmO08uESS-pTLmoidqPE--I',
}

for i in range(1000):
    response = requests.get('http://localhost:8080/auth/me', headers=headers)
    print(response.text)

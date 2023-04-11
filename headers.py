import requests
API_KEY = "f13fe3a3f1ea67d9a1c15d549efc719e"
url = 'https://api.the-odds-api.com/v4/sports/?apiKey='+ API_KEY
r = requests.get(url)
print(r.headers)
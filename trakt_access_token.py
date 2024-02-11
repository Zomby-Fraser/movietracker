import requests

# Replace with your actual details
client_id = '472a8c2f7988932746210823828708957e6705c59e8246c9f58ce6cc44ce2dce'
client_secret = '5e7e403134b94a02f626d750a92d476cff50c8a803e23e5b21f7dada4de86543'
redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
code = '192D997A'

data = {
    'code': code,
    'client_id': client_id,
    'client_secret': client_secret,
    'redirect_uri': redirect_uri,
    'grant_type': 'authorization_code'
}

response = requests.post('https://api.trakt.tv/oauth/token', data=data)
token_info = response.json()

print(token_info)

import requests

WOLFRAM_APP_ID = "A24U8GXLAU"

def wolfram_query(question):
    """wolfram_query - Auto-documented by self-evolution."""
    try:
        r = requests.get('https://api.wolframalpha.com/v2/query',
            params={'input': question, 'appid': WOLFRAM_APP_ID, 'output': 'json'}, timeout=10)
        data = r.json()['queryresult']
        if data.get('success'):
            results = []
            primary = None
            for pod in data.get('pods', []):
                text = pod.get('subpods', [{}])[0].get('plaintext', '')
                if text:
                    results.append((pod['title'], text))
                if pod.get('primary') and text:
                    primary = text
            return {'success': True, 'primary': primary, 'pods': results}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    return {'success': False, 'error': 'No result'}

if __name__ == "__main__":
    print(wolfram_query("2+7"))
    print(wolfram_query("mass of the sun"))
    print(wolfram_query("integrate x^2 dx"))

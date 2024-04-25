import http.client
import logging

_logger = logging.getLogger(__name__)

def checkout(encencryptedText, url, access_code, env):

    url = url.replace("https://", "").replace("http://", "")
    conn = http.client.HTTPSConnection(url)

    if env != 'production':
        _logger.info('Hesabe: Payment URL: ' +  url) 
        _logger.info('Hesabe: Encrypted: ' +  encencryptedText)
        _logger.info('Hesabe: access code: ' +  access_code)

    dataList = []
    boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
    dataList.append('--' + boundary)
    dataList.append('Content-Disposition: form-data; name=data;')
    dataList.append('Content-Type: {}'.format('text/plain'))
    dataList.append('')
    dataList.append(encencryptedText)
    dataList.append('--'+boundary+'--')
    dataList.append('')
    body = '\r\n'.join(dataList)
    payload = body.encode('utf-8')
    
    headers = {
        'accesscode': access_code,
        'Cookie': 'api_20_hesabe_payment_collection_company_session=eyJpdiI6IjFxVDc3YWJ1MFNZcUFrNnVzbkdUMnc9PSIsInZhbHVlIjoiWEtwcDVrSmY0MlQvK255ZDBIZEdUWXE5ZHFvMWNzcVJYc0NyZStQVFQvS3hqRGJBZkF4aThGWWEvR1dSbytUWklicEdqdnB4dXJ6bmJkUlZ6WmlwSjh4dElHcGZTaElDb1UvR3ZVT0V3VGcvQlBmQ205ZCs4VkRtUEM4Vi9kK2oiLCJtYWMiOiI1MGYzYjk3MWMwMjYzZjE5Mzg3M2IyMzRmMWM4YzcwY2JiN2NiODc1MThjOWI0YzFmNmM5OTg0ZDAxNTc1ZWU2IiwidGFnIjoiIn0%3D',
        'Content-type': 'multipart/form-data; boundary={}'.format(boundary)
    }

    conn.request("POST", "/checkout", payload, headers)
    res = conn.getresponse()
    data = res.read()

    if env != 'production':
        _logger.info('Hesabe: Response: ' +  data.decode("utf-8"))

    return data.decode("utf-8").strip()
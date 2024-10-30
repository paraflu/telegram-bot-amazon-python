import os
import aiohttp

from .log import log



class ShortenLinks:

    SHORTEN_LINKS = os.environ.get('SHORTEN_LINKS', 'false').lower() == 'true'
    BITLY_TOKEN = os.environ.get('BITLY_TOKEN')

    async def shorten_url(self, url):
        headers = {
            'Authorization': f'Bearer {ShortenLinks.BITLY_TOKEN}',
            'Content-Type': 'application/json',
        }
        body = {'long_url': url, 'domain': 'bit.ly'}
        async with aiohttp.ClientSession() as session:
            async with session.post('https://api-ssl.bitly.com/v4/shorten', headers=headers, json=body) as response:
                result = await response.json()
                if 'link' in result:
                    return result['link']
                else:
                    log(f"Error in bitly response {result}")
                    return url

import os
import re


class AliExpressSettings:
    """
    AliExpress share

    full
    https://it.aliexpress.com/item/1005007703420314.html?spm=a2g0o.detail.0.0.75deg6EQg6EQ7L&mp=1&gatewayAdapt=glo2ita

    short
    https://s.click.aliexpress.com/e/_Exe8PSp
    """

    # Regex patterns
    FULL_URL_REGEX = re.compile(r'https?://(([^\s]*)\.)?aliexpress\.([a-z.]{2,5})/item/(?P<asin>\d+).html\?[^\s]*', re.IGNORECASE)
    SHORT_URL_REGEX = re.compile(r'https?://s.click.aliexpress.com/e/([a-zA-Z0-9_]+)', re.IGNORECASE)
    URL_REGEX = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)', re.IGNORECASE)
    STORE = 'AliExpress'
    STORE_TAG = os.environ.get('STORE_TAG')
    STORE_TLD = os.environ.get('STORE_TLD', 'com')
    RAW_URL_REGEX = re.compile(f'https?://(([^\\s]*)\\.)?aliexpress\\.{STORE_TLD}/?([^\\s]*)', re.IGNORECASE)

    @staticmethod
    def build_affiliate_url(asin: str) -> str:
        return f'https://it.aliexpress.{AliExpressSettings.STORE_TLD}/item/{asin}.html?tag={AliExpressSettings.STORE_TAG}'

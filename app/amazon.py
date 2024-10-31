import os
import re


class AmazonSettings:

    # Regex patterns
    FULL_URL_REGEX = re.compile(r'https?://(([^\s]*)\.)?amazon\.([a-z.]{2,5})(\/d\/([^\s]*)|\/([^\s]*)\/?(?:dp|o|gp|-)\/)(aw\/d\/|product\/)?(?P<asin>B[0-9A-Z]{9})([^\s]*)', re.IGNORECASE)
    SHORT_URL_REGEX = re.compile(r'https?://(([^\s]*)\.)?(amzn\.to|amzn\.eu)(/d)?/([0-9A-Za-z]+)', re.IGNORECASE)
    URL_REGEX = re.compile(r'https?:\/\/(www\.)?[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&//=]*)', re.IGNORECASE)
    STORE_TAG = os.environ.get('STORE_TAG')
    STORE_TLD = os.environ.get('STORE_TLD', 'com')
    RAW_URL_REGEX = re.compile(f'https?://(([^\\s]*)\\.)?amazon\\.{STORE_TLD}/?([^\\s]*)', re.IGNORECASE)

    @staticmethod
    def build_affiliate_url(asin: str) -> str:
        return f'https://www.amazon.{AmazonSettings.STORE_TLD}/dp/{asin}?tag={AmazonSettings.STORE_TAG}'

import asyncio
from datetime import datetime
import logging
import unittest

import pytest
from telegram import Chat, Message, Update, User

from app import AffiliateMessageHandler
from app.aliexpress import AliExpressSettings
from app.amazon import AmazonSettings
logging.basicConfig(level=logging.DEBUG)


class MockHandler(AffiliateMessageHandler):
    def __init__(self):
        super().__init__()
        amazonSettingCustom = AmazonSettings
        amazonSettingCustom.STORE_TAG = 'TEST'
        aliSettings = AliExpressSettings
        aliSettings.STORE_TAG = 'TEST_ALI'
        self.affiliates = [
            amazonSettingCustom,
            aliSettings
        ]
        self.last_message = ''

    async def handle_message(self, update: Update, context):
        self.last_message = update.message.text
        await super().handle_message(update, context)

    async def delete_and_send(self, update, context, text) -> bool:
        logging.debug(f'send {text}')
        self.last_message = text
        return True


def make_message(message: str) -> Update:
    return Update(message=Message(message_id=43, text=message, from_user=User(id=9, first_name='name', is_bot=False),
                                  date=datetime.now(), chat=Chat(id=2, username='user', type='group')), update_id=1)


class TestMessageHandler(unittest.IsolatedAsyncioTestCase):

    async def test_simple_message_without_link(self):
        h = MockHandler()
        await h.handle_message(
            make_message('test'),
            {}
        )

        self.assertEqual(h.last_message, 'test')

    async def test_simple_message_with_link(self):
        h = MockHandler()
        await h.handle_message(
            make_message('see this product! https://www.amazon.it/Xiaomi-Aspirapolvere-Lavapavimenti-Autosvuotamento-Aspirazione/dp/B0BW4LVTTD?crid=2LNSCK9J3HQJ9&dib=eyJ2IjoiMSJ9.dZxJKspNfsNblp1QM7ZbYGQmCqV5J49Iw1e8DRkZmLGAIit1fx5tn2g1zp5NyOPzqRK1R1DeHVHOCAl88mqeHxsiVCXOKyiO7UjAP3TAnPFnXO-qYaFVaAqB8Wp0pKFnwqz1yj2aITjVjJBvxbDO3s1VDxNs9xtYOOL7LWLTWW07tMZVqOtOFKsLQlTWp10tb6bfx1RwxJgUMcwYtYFfkPOOyVGLm7fuyfZjWqkLilY.JoQoL7eLKKUbcG8lcpzDVED_8RQhyoa3arHaCVN-Cdk&dib_tag=se&keywords=robot%2Blavapavimenti%2Be%2Baspirapolvere&qid=1730369422&s=kitchen&sprefix=robot%2Blava%2Ckitchen%2C121&sr=1-9&ufe=app_do%3Aamzn1.fos.9d4f9b77-768c-4a4e-94ad-33674c20ab35&th=1'),
            {}
        )

        self.assertEqual(h.last_message, 'Message by name  with Amazon affiliate link:\n\nsee this product! https://www.amazon.com/dp/B0BW4LVTTD?tag=TEST')

    async def test_aliexpress_link(self):
        h = MockHandler()
        await h.handle_message(
            make_message('see this product! https://it.aliexpress.com/item/1005007703420314.html?spm=a2g0o.home.0.0.120d6a5488Vp88&mp=1&gatewayAdapt=glo2ita'),
            {}
        )

        self.assertEqual(h.last_message, 'Message by name  with Amazon affiliate link:\n\nsee this product! https://it.aliexpress.com/item/1005007703420314.html?tag=TEST_ALI')


if __name__ == '__main__':
    unittest.main()

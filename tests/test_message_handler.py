import logging
import unittest

from app import AffiliateMessageHandler
logging.basicConfig(level=logging.DEBUG)

class MockHandler(AffiliateMessageHandler):
    
    def delete_and_send(self, update, context, text):
        logging.debug(f'send {text}')
        self.last_message = text
        
class TestMessageHandler(unittest.TestCase):
    def test_message(self):
        h = MockHandler()
        h.handle_message(
            {
                'message': 'test'
            }
        )
        
        self.assertEqual(h.last_message, 'test')

if __name__ == '__main__':
    unittest.main()

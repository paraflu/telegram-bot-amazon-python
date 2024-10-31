from datetime import datetime
import os
import re
import sys
from urllib.parse import parse_qs, urlencode, urlparse
import aiohttp
from telegram import Update, Chat

from .amazon import AmazonSettings
from .log import log
from .shorten_links import ShortenLinks


class AffiliateMessageHandler:

    ALI_TAG = os.environ.get('ALI_TAG')
    ALI_TLD = os.environ.get('ALI_TLD', 'com')

    CHANNEL_NAME = os.environ.get('CHANNEL_NAME')

    RAW_LINKS = os.environ.get('RAW_LINKS', 'false').lower() == 'true'
    CHECK_FOR_REDIRECTS = os.environ.get(
        'CHECK_FOR_REDIRECTS', 'false').lower() == 'true'
    CHECK_FOR_REDIRECT_CHAINS = os.environ.get(
        'CHECK_FOR_REDIRECT_CHAINS', 'false').lower() == 'true'
    MAX_REDIRECT_CHAIN_DEPTH = int(
        os.environ.get('MAX_REDIRECT_CHAIN_DEPTH', 2))
    GROUP_REPLACEMENT_MESSAGE = os.environ.get(
        'GROUP_REPLACEMENT_MESSAGE', 'Message by {USER} with {STORE} affiliate link:\n\n{MESSAGE}')

    # Users to ignore
    USERNAMES_TO_IGNORE = [username.lower() for username in os.environ.get(
        'IGNORE_USERS', '').split(',') if username.startswith('@')]
    USER_IDS_TO_IGNORE = [int(user_id) for user_id in os.environ.get(
        'IGNORE_USERS', '').split(',') if user_id.isdigit()]

    def __init__(self):
        self.affiliates = [
            AmazonSettings
        ]

    # def build_affiliate_url(self, affiliate, asin):
    #     return f'https://www.amazon.{affiliate.STORE_TLD}/dp/{asin}?tag={affiliate.STORE_TAG}'

    def build_raw_affiliate_url(element):
        url = element.get('expanded_url') or element['full_url']
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        query['tag'] = [AffiliateMessageHandler.AMAZON_TAG]
        new_query = urlencode(query, doseq=True)
        return parsed_url._replace(query=new_query).geturl()

    async def get_affiliate_url(self, affiliate, element):
        url = affiliate.build_affiliate_url(element['asin']) if element.get(
            'asin') else self.build_raw_affiliate_url(element)
        return await ShortenLinks.shorten_url(url) if ShortenLinks.SHORTEN_LINKS else url

    async def get_long_url(self, short_url: str, chain_depth=0):
        try:
            chain_depth += 1
            async with aiohttp.ClientSession() as session:
                async with session.get(short_url, allow_redirects=False) as response:
                    if response.status in [301, 302, 303, 307, 308]:
                        full_url = response.headers.get('location')
                        if AffiliateMessageHandler.CHECK_FOR_REDIRECT_CHAINS and chain_depth < AffiliateMessageHandler.MAX_REDIRECT_CHAIN_DEPTH:
                            next_redirect = await self.get_long_url(full_url, chain_depth)
                            return {
                                'full_url': next_redirect['full_url'],
                                'short_url': short_url
                            }
                        else:
                            return {
                                'full_url': full_url,
                                'short_url': short_url
                            }
                    else:
                        # If there is no redirection, consider the original URL as the full URL
                        return {
                            'full_url': short_url,
                            'short_url': short_url
                        }
        except Exception as e:
            log(f"Short URL {short_url} -> ERROR: {e}")
            return None

    def get_asin_from_full_url(self, url: str, full_reg_exp: re):
        match = full_reg_exp.search(url)
        return match.group(8) if match else url

    def build_mention(self, user):
        return f"@{user.username}" if user.username else f"{user.first_name} {user.last_name or ''}"

    def is_group(self, chat: Chat):
        return chat.type in ['group', 'supergroup']

    async def build_message(self, chat, message, replacements, user):
        if self.is_group(chat):
            affiliate_message = message
            for element in replacements:
                for replacement in replacements:
                    sponsored_url = await self.get_affiliate_url(replacement['affiliate'], element)
                    affiliate_message = affiliate_message.replace(
                        element['full_url'], sponsored_url)
            return AffiliateMessageHandler.GROUP_REPLACEMENT_MESSAGE.replace('\\n', '\n').replace('{USER}', self.build_mention(user)).replace('{STORE}', 'Amazon').replace('{MESSAGE}', affiliate_message).replace('{ORIGINAL_MESSAGE}', message)
        else:
            if len(replacements) > 1:
                text = '\n'.join(f"• {await self.get_affiliate_url(replacements['affiliate'],
                                                                   element)}" for element in replacements)
            else:
                text = await self.get_affiliate_url(replacements['affiliate'], replacements[0])
            return text

    async def delete_and_send(self, update: Update, context, text):
        chat = update.message.chat
        message_id = update.message.message_id
        chat_id = chat.id
        deleted = False

        if self.is_group(chat):
            await context.bot.delete_message(chat_id, message_id)
            deleted = True

        reply_to_message_id = update.message.reply_to_message.message_id if update.message.reply_to_message else None

        if update.message.caption and self.is_group(chat):
            await context.bot.send_photo(chat_id, update.message.photo[-1].file_id, caption=text, reply_to_message_id=reply_to_message_id)
            if AffiliateMessageHandler.CHANNEL_NAME:
                await context.bot.send_photo(AffiliateMessageHandler.CHANNEL_NAME, update.message.photo[-1].file_id, caption=text, reply_to_message_id=reply_to_message_id)
        else:
            await context.bot.send_message(chat_id, text, reply_to_message_id=reply_to_message_id)
            if AffiliateMessageHandler.CHANNEL_NAME:
                await context.bot.send_message(AffiliateMessageHandler.CHANNEL_NAME, text, reply_to_message_id=reply_to_message_id)

        return deleted

    def replace_text_links(self, message):
        if message.entities:
            text = message.text
            offset_shift = 0
            for entity in message.entities:
                if entity.type == 'text_link':
                    offset = entity.offset + offset_shift
                    length = entity.length
                    new_text = text[:offset] + \
                        entity.url + text[offset + length:]
                    offset_shift += len(entity.url) - length
                    text = new_text
            return text
        return message.text

    async def handle_message(self, update: Update, context):
        try:
            msg = update.message
            from_username = msg.from_user.username.lower() if msg.from_user.username else ""
            from_id = msg.from_user.id

            if (from_username not in AffiliateMessageHandler.USERNAMES_TO_IGNORE and from_id not in AffiliateMessageHandler.USER_IDS_TO_IGNORE) or not self.is_group(msg.chat):
                text = self.replace_text_links(msg)
                text = text or msg.caption
                caption_saved_as_text = text == msg.caption

                if AffiliateMessageHandler.CHECK_FOR_REDIRECTS:
                    long_url_replacements = []
                    for affiliate in self.affiliates:
                        for match in affiliate.URL_REGEX.finditer(text):
                            if not affiliate.SHORT_URL_REGEX.match(match.group()) and not affiliate.RAW_URL_REGEX.match(match.group()):
                                log(f"Found non-Amazon URL {match.group()}")
                                long_url = await self.get_long_url(match.group())
                                long_url_replacements.append(long_url)

                    for element in long_url_replacements:
                        if element and element['full_url']:
                            text = text.replace(
                                element['short_url'], element['full_url'])

                replacements = []
                if AffiliateMessageHandler.RAW_LINKS:
                    for affiliate in self.affiliates:
                        for match in affiliate.RAW_URL_REGEX.finditer(text):
                            replacements.append(
                                {'affiliate': affiliate, 'asin': None, 'full_url': match.group()})
                else:
                    for affiliate in self.affiliates:
                        for match in affiliate.FULL_URL_REGEX.finditer(text):
                            replacements.append(
                                {'affiliate': affiliate, 'asin': match.group('asin'), 'full_url': match.group()})

                for affiliate in self.affiliates:
                    for match in affiliate.SHORT_URL_REGEX.finditer(text):
                        short_url = match.group()
                        url = await self.get_long_url(short_url)
                        if url:
                            if AffiliateMessageHandler.RAW_LINKS:
                                replacements.append(
                                    {'affiliate': affiliate, 'asin': None, 'expanded_url': url['full_url'], 'full_url': short_url})
                            else:
                                asin = self.get_asin_from_full_url(url['full_url'], affiliate.FULL_URL_REGEX)
                                if not asin or asin == url['full_url']:
                                    # If I cannot extract the ASIN, I'll try to get it from the short URL
                                    # Group 5 should contain the identifier after /d/
                                    asin = match.group(5)
                                replacements.append(
                                    {'affiliate': affiliate, 'asin': asin, 'full_url': short_url})

                if replacements:
                    text = await self.build_message(msg.chat, text, replacements, msg.from_user)
                    deleted = await self.delete_and_send(update, context, text)

                    if len(replacements) > 1:
                        for element in replacements:
                            log(f"Long URL {element['full_url']} -> ASIN {element['asin']} from {
                                self.build_mention(msg.from_user)}{' (original message deleted)' if deleted else ''}")
                    else:
                        log(f"Long URL {replacements[0]['full_url']} -> ASIN {replacements[0]['asin']} from {
                            self.build_mention(msg.from_user)}{' (original message deleted)' if deleted else ''}")
            else:
                log(f"Ignored message from {self.build_mention(
                    msg.from_user)} because it is included in the IGNORE_USERS env variable")
        except Exception as e:
            log("ERROR, please file a bug report at https://github.com/gioxx/telegram-bot-amazon-python")
            print(e)

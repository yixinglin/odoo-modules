from openai import OpenAI
import markdown  # Add this import for markdown conversion
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import html_sanitize  # Import for HTML sanitization
import logging

_logger = logging.getLogger(__name__)

class Channel(models.Model):
    _inherit = 'discuss.channel'

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        rdata = super(Channel, self)._notify_thread(message, msg_vals=msg_vals, **kwargs)
        chatgpt_channel_id = self.env.ref('is_chatgpt_integration.channel_chatgpt')
        user_chatgpt = self.env.ref("is_chatgpt_integration.user_chatgpt")
        partner_chatgpt = self.env.ref("is_chatgpt_integration.partner_chatgpt")
        author_id = msg_vals.get('author_id')
        chatgpt_name = str(partner_chatgpt.name or '') + ', '
        prompt = msg_vals.get('body')

        if not prompt:
            return rdata
        
        ICP = self.env['ir.config_parameter'].sudo()
        temperature = float(ICP.get_param('is_chatgpt_integration.temperature', default=0.7))  # Determines the level of creativity in the response. A higher temperature results in more creative responses, but also more conversational style.
        max_history = int(ICP.get_param('is_chatgpt_integration.max_history', default=10))  # Determines the maximum number of previous messages to use as context for the response. A higher number results in more context, but also more repetition.  # Maximum number of previous messages to include in the prompt
        
        _logger.info(f"Using temperature {temperature} and max_history {max_history} for ChatGPT integration.")
        _logger.info(prompt)

        try:
            if author_id != partner_chatgpt.id and (chatgpt_name in msg_vals.get('record_name', '') or 'ChatGPT,' in msg_vals.get('record_name', '')) and self.channel_type == 'chat':
                # Build conversation history
                messages = self._get_conversation_history(partner_chatgpt, max_history)                
                messages.append({"role": "user", "content": prompt})
                res = self._get_chatgpt_response(messages=messages, temperature=temperature)
                _logger.info(f"ChatGPT response: {res}")
                # Convert markdown to HTML and sanitize                
                res_html = self._markdown_to_html(res)
                res_html = html_sanitize(res_html)                
                self.with_user(user_chatgpt).message_post(
                    body=res_html,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',                    
                )
            elif author_id != partner_chatgpt.id and msg_vals.get('model', '') == 'discuss.channel' and msg_vals.get('res_id', 0) == chatgpt_channel_id.id:
                # Build conversation history
                messages = self._get_conversation_history(partner_chatgpt, max_history)
                messages.append({"role": "user", "content": prompt})
                res = self._get_chatgpt_response(messages=messages, temperature=temperature)                
                _logger.info(f"ChatGPT response: {res}")
                # Convert markdown to HTML and sanitize                
                res_html = self._markdown_to_html(res)
                res_html = html_sanitize(res_html)
                chatgpt_channel_id.with_user(user_chatgpt).message_post(
                    body=res_html,
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',                 
                )                

        except Exception as e:
            # Log or handle exceptions more specifically
            pass

        return rdata

    def _get_conversation_history(self, partner_chatgpt, max_history):
        # 获取所有消息并按日期降序排列
        all_messages = self.message_ids.sorted(key=lambda m: m.date, reverse=True)
        
        messages = []
        latest_chatgpt_message = None
        user_messages = []

        # 遍历消息，保留所有用户的消息，并找到最新的一条 ChatGPT 消息
        for msg in all_messages:
            if msg.author_id == partner_chatgpt:
                if not latest_chatgpt_message:
                    latest_chatgpt_message = msg  # 只保留最新的一条 ChatGPT 回复
            else:
                user_messages.append(msg)

            # 当消息数达到 max_history 时停止
            if len(user_messages) + (1 if latest_chatgpt_message else 0) >= max_history:
                break

        # 保证用户消息按照时间顺序排列
        user_messages = reversed(user_messages)

        # 将用户消息添加到对话中
        for msg in user_messages:
            content = msg.body or ''
            content = self._clean_html_tags(content)  # 去除 HTML 标签
            messages.append({'role': 'user', 'content': content})

        # 添加最新的 ChatGPT 消息
        if latest_chatgpt_message:
            content = latest_chatgpt_message.body or ''
            content = self._clean_html_tags(content)
            messages.append({'role': 'assistant', 'content': content})

        return messages

    def _get_chatgpt_response(self, messages, temperature):
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('is_chatgpt_integration.openapi_api_key')
        gpt_model_id = ICP.get_param('is_chatgpt_integration.chatgp_model')
        gpt_model = 'gpt-3.5-turbo'
        try:
            if gpt_model_id:
                gpt_model = self.env['chatgpt.model'].browse(int(gpt_model_id)).name
        except Exception as ex:
            gpt_model = 'gpt-3.5-turbo'
            pass
        try:
            client = OpenAI(api_key=api_key)            
            _logger.info(f"Using {gpt_model} model for ChatGPT integration.")
            response = client.chat.completions.create(
                messages=messages,
                model=gpt_model,
                temperature=temperature
            )
            response_message = response.choices[0].message.content
            return response_message
        except Exception as e:
            raise UserError(_(e))

    def _clean_html_tags(self, text):
        # Utility method to strip HTML tags from text
        from odoo.tools import html2plaintext
        return html2plaintext(text)
    
    def _markdown_to_html(self, md_text):
        # Utility method to convert markdown to HTML
        # Define the extensions you want to use, including table and code highlighting
        extensions = [
            'markdown.extensions.tables',  # Support for tables
            'markdown.extensions.fenced_code',  # Support for fenced code blocks
            'markdown.extensions.codehilite',  # Code highlighting
            'markdown.extensions.extra',  # Supports additional Markdown features like definition lists, footnotes
        ]        
        # Convert Markdown to HTML
        html = markdown.markdown(md_text, extensions=extensions)        
        return html


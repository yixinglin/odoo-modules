# -*- coding: utf-8 -*-
# Copyright (c) 2020-Present InTechual Solutions. (<https://intechualsolutions.com/>)

# from odoo import fields, models


# class ResConfigSettings(models.TransientModel):
#     _inherit = "res.config.settings"

#     def _get_default_chatgpt_model(self):
#         return self.env.ref('is_chatgpt_integration.chatgpt_model_gpt_3_5_turbo').id

#     openapi_api_key = fields.Char(string="API Key", help="Provide the API key here", config_parameter="is_chatgpt_integration.openapi_api_key")
#     chatgpt_model_id = fields.Many2one('chatgpt.model', 'ChatGPT Model', ondelete='cascade', default=_get_default_chatgpt_model,  config_parameter="is_chatgpt_integration.chatgp_model")


from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def _get_default_chatgpt_model(self):
        return self.env.ref('is_chatgpt_integration.chatgpt_model_gpt_3_5_turbo').id
        
    openapi_api_key = fields.Char(
        string="API Key",
        help="Provide the API key here",
        config_parameter="is_chatgpt_integration.openapi_api_key"
    )
    
    chatgpt_model_id = fields.Many2one(
        'chatgpt.model',
        'ChatGPT Model',
        ondelete='cascade',
        config_parameter="is_chatgpt_integration.chatgpt_model",
        default=_get_default_chatgpt_model,
    )

    temperature = fields.Float(
        string="Temperature", 
        help="The level of creativity in the response. Higher values make responses more creative.",
        config_parameter="is_chatgpt_integration.temperature",
        default=0.7
    )
    
    max_history = fields.Integer(
        string="Max History",
        help="Maximum number of previous messages to include in the prompt.",
        config_parameter="is_chatgpt_integration.max_history",
        default=10
    )



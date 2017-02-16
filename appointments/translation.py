from modeltranslation.translator import register, TranslationOptions
from .models import MessageTemplate


@register(MessageTemplate)
class MessageTemplateTranslationOptions(TranslationOptions):
    fields = ('content', 'content_tail')

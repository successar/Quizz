from django import template

register = template.Library()

@register.filter
def answer_choice_to_string(question, answer):
    return question.answer_choice_to_string(answer)

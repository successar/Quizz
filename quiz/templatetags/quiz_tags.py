from django import template

register = template.Library()

@register.filter
def answer_choice_to_string(question, answer):
    return question.answer_choice_to_string(answer)

@register.filter(name='addcss')
def addcss(field, css):
	class_old = field.field.widget.attrs.get('class', None)
	class_new = class_old + ' ' + css if class_old else css
	return field.as_widget(attrs={"class": class_new})
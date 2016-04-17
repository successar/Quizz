from django import forms
from django.forms.widgets import RadioSelect, Textarea
from .models import Question, Answer
from django.forms.models import inlineformset_factory


class QuestionForm(forms.Form):
    def __init__(self, question, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        choice_list = [x for x in question.get_answers_list()]
        self.fields["answers"] = forms.ChoiceField(choices=choice_list,
                                                   widget=RadioSelect)


AnswerFormSet = inlineformset_factory(Question, Answer, fields=('content', 'correct',), can_delete=True)
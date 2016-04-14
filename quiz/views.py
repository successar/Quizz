import random

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, FormView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import QuestionForm
from .models import Quiz, Category, Progress, Sitting, Question

class QuizMarkerMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(QuizMarkerMixin, self).dispatch(*args, **kwargs)


class CategoriesListView(ListView):
    template_name='CategoryList.html'
    model = Category


class ViewQuizListByCategory(ListView):
    model = Quiz
    template_name = 'QuizListTheme.html'

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(Category, category=self.kwargs['category_name'])

        return super(ViewQuizListByCategory, self).\
            dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ViewQuizListByCategory, self)\
            .get_context_data(**kwargs)

        context['category'] = self.category
        return context

    def get_queryset(self):
        queryset = super(ViewQuizListByCategory, self).get_queryset()
        return queryset.filter(category=self.category)


class QuizUserProgressView(TemplateView):
    template_name = 'ProgressTheme.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(QuizUserProgressView, self)\
            .dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuizUserProgressView, self).get_context_data(**kwargs)
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        context['exams'] = progress.show_exams()
        return context


class QuizMarkingDetail(QuizMarkerMixin, DetailView):
    model = Sitting
    template_name='SittingTheme.html'

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()

        q_to_toggle = request.POST.get('qid', None)
        if q_to_toggle:
            q = Question.objects.get(id=int(q_to_toggle))
            if int(q_to_toggle) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(q)
            else:
                sitting.add_incorrect_question(q)

        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context['questions'] =\
            context['sitting'].get_questions(with_answers=True)
        return context


class QuizTake(FormView):
    form_class = QuestionForm
    template_name = 'QuestionTheme.html'

    ### Get the request In , Dispatch to appropriate handler ####
    def dispatch(self, request, *args, **kwargs):
        print("dispatch")
        self.quiz = get_object_or_404(Quiz, url=self.kwargs['quiz_name'])

        self.logged_in_user = self.request.user.is_authenticated()

        if self.logged_in_user:
            self.sitting = Sitting.objects.user_sitting(request.user,
                                                        self.quiz)
        else:
            raise PermissionDenied

        return super(QuizTake, self).dispatch(request, *args, **kwargs)
        
    ### Instantiate Question form to be sent back using HTTP Response after previous POST data is processed ###
    def get_form(self, form_class):
        print("get_form")
        if self.logged_in_user:
            self.question = self.sitting.get_first_question()
            self.progress = self.sitting.progress()
        else:
            raise PermissionDenied

        return form_class(**self.get_form_kwargs()) ### takes self.question and instantiate a QuestionForm ###
    
    ### Return keyword arguments to instantiate the form ###
    def get_form_kwargs(self):
        print("get_form_kwargs")
        kwargs = super(QuizTake, self).get_form_kwargs()

        return dict(kwargs, question=self.question)
    
    ### Called if POST Request Data is valid. If questions are exhausted, return final results ###
    ### It works alongwith form_valid_user below to update user score and proceed to next question ###
    def form_valid(self, form):
        print("form_valid")
        if self.logged_in_user:
            self.form_valid_user(form) ### Update score if correct, update question list ###
            if self.sitting.get_first_question() is False:  ### All questions are answered, Display final results ###
                return self.final_result_user()
        else:
            raise PermissionDenied
            
        self.request.POST = {}

        return super(QuizTake, self).get(self, self.request) ### Generate next question response using get_context_data above ###
                                                             ### and send back a HTTP response using QuestionTheme.html template.  ###

    ### Set any variables to be used in template , Used by above. ###
    ### Also calls get_form to instantiate the form and adds it to the context ###
    def get_context_data(self, **kwargs):
        print("get_context_data")
        context = super(QuizTake, self).get_context_data(**kwargs)
        context['question'] = self.question
        context['quiz'] = self.quiz
        if hasattr(self, 'progress'):
            context['progress'] = self.progress
        return context
    
    ### Called if POST Request Data is valid . Add 1 to score if answer was correct, update question list of current quiz ###
    def form_valid_user(self, form):
        print("form form_valid_user")
        progress, c = Progress.objects.get_or_create(user=self.request.user)
        guess = form.cleaned_data['answers']
        is_correct = self.question.check_if_correct(guess)

        if is_correct is True:
            self.sitting.add_to_score(1)
        else:
            self.sitting.add_incorrect_question(self.question)

        self.sitting.add_user_answer(self.question, guess)
        self.sitting.remove_first_question()
    
    ### If all questions are answered, generate final results and send back HTTP Response using ResultTheme.html template ###
    def final_result_user(self):
        print("final_result_user")
        results = {
            'quiz': self.quiz,
            'score': self.sitting.get_current_score,
            'max_score': self.sitting.get_max_score,
            'percent': self.sitting.get_percent_correct,
            'sitting': self.sitting,
        }

        self.sitting.mark_quiz_complete()

        results['questions'] =\
              self.sitting.get_questions(with_answers=True)
        results['incorrect_questions'] =\
              self.sitting.get_incorrect_questions

        return render(self.request, 'ResultTheme.html', results)


class QuizCreate(LoginRequiredMixin, CreateView):
    model = Quiz
    template_name = 'QuizCreate.html'
    fields = ['title', 'description', 'category', 'pass_mark']
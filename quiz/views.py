import random

from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, render, render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, FormView
from django.views.generic.edit import CreateView, UpdateView, BaseUpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from .forms import QuestionForm, AnswerFormSet
from .models import Quiz, Category, Progress, Sitting, Question
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse_lazy
from friendship.models import Friend
from django.db.models import Q, Count
import datetime
from datetime import timedelta
from copy import deepcopy

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
        friends = Friend.objects.friends(self.request.user).values_list('from_user', flat=True)
        return queryset.filter(Q(category=self.category), Q(user__in=friends)|Q(user=self.request.user), Q(is_active=True))


class QuizUserProgressView(TemplateView):
    template_name = 'ProgressTheme.html'

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(QuizUserProgressView, self).dispatch(request, *args, **kwargs)

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
        return self.get(request)

    def get_context_data(self, **kwargs):
        context = super(QuizMarkingDetail, self).get_context_data(**kwargs)
        context['questions'] = context['sitting'].get_questions(with_answers=True)
        return context


class QuizTake(FormView):
    form_class = QuestionForm
    template_name = 'QuestionTheme.html'

    ### Get the request In , Dispatch to appropriate handler ####
    def dispatch(self, request, *args, **kwargs):
        print("dispatch")
        self.quiz = get_object_or_404(Quiz, id=self.kwargs['quiz_name'], is_active=True)

        self.logged_in_user = self.request.user.is_authenticated()

        if self.logged_in_user:
            try :
                self.sitting = Sitting.objects.user_sitting(request.user, self.quiz)
            except ImproperlyConfigured as e:
                return render(request, "Error.html", { "error" : "%s" % e })
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
    success_url = reverse_lazy('question_create')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        self.request.session['quizid'] = self.object.id
        self.request.session['quizname'] = self.object.title
        if self.object.category :
            self.request.session['quizcategoryid'] = self.object.category.id
            self.request.session['quizcategory'] = self.object.category.category
        return HttpResponseRedirect(self.get_success_url())


class QuestionCreate(LoginRequiredMixin, CreateView):
    model = Question
    template_name = 'QuestionCreate.html'
    fields = ['figure', 'content', 'explanation']

    def get_success_url(self):
        return reverse_lazy('question_list', kwargs={'quiz_url' : self.request.session['quizid']})

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        answer_form = AnswerFormSet()
        return self.render_to_response(
            self.get_context_data(form=form,
                                  answer_form=answer_form))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance and its inline
        formsets with the passed POST variables and then checking them for
        validity.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        answer_form = AnswerFormSet(self.request.POST)
        if (form.is_valid() and answer_form.is_valid()):
            return self.form_valid(form, answer_form)
        else:
            return self.form_invalid(form, answer_form)

    def form_valid(self, form, answer_form):
        """
        Called if all forms are valid. Creates a Question instance along with
        associated Answers and then redirects to a
        success page.
        """
        self.object = form.save(commit=False)
        if 'quizid' in self.request.session :
            self.object.quiz = Quiz.objects.get(id=int(self.request.session['quizid']))
        print(self.object)
        self.object.save()
        answer_form.instance = self.object
        answer_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, answer_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(
            self.get_context_data(form=form,
                                  answer_form=answer_form))


class QuestionUpdate(LoginRequiredMixin, UpdateView):
    model = Question
    template_name = 'QuestionUpdate.html'
    fields = ['figure', 'content', 'explanation']

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests and instantiates blank versions of the form
        and its inline formsets.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        answer_form = AnswerFormSet(instance=self.object)
        return self.render_to_response(self.get_context_data(form=form,answer_form=answer_form))

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance and its inline
        formsets with the passed POST variables and then checking them for
        validity.
        """
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        answer_form = AnswerFormSet(self.request.POST, instance=self.object)
        if (form.is_valid() and answer_form.is_valid()):
            return self.form_valid(form, answer_form)
        else:
            return self.form_invalid(form, answer_form)

    def form_valid(self, form, answer_form):
        """
        Called if all forms are valid. Creates a Question instance along with
        associated Answers and then redirects to a
        success page.
        """
        self.object = form.save()
        answer_form.instance = self.object
        answer_form.save()
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form, answer_form):
        """
        Called if a form is invalid. Re-renders the context data with the
        data-filled forms and errors.
        """
        return self.render_to_response(self.get_context_data(form=form,answer_form=answer_form))

    def get_success_url(self) :
        return reverse_lazy('question_list', kwargs={'quiz_url' : self.kwargs['quiz_url']})


class QuestionList(LoginRequiredMixin, ListView):
    template_name = 'QuestionList.html'
    model = Question

    def dispatch(self, request, *args, **kwargs):
        self.quiz = get_object_or_404(Quiz, id=self.kwargs['quiz_url'], is_active=True)
        return super(QuestionList, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(QuestionList, self).get_context_data(**kwargs)
        context['quiz'] = self.quiz
        return context

    def get_queryset(self):
        queryset = super(QuestionList, self).get_queryset()
        return queryset.filter(quiz=self.quiz) 


class QuizUpdate(LoginRequiredMixin, UpdateView):
    model = Quiz
    template_name = 'QuizCreate.html'
    fields = ['title', 'description', 'category', 'pass_mark']

    def duplicate(self, quiz, new_quiz):
        for question in quiz.question_set.all() :
            question_copy = deepcopy(question)
            question_copy.id = None
            question_copy.quiz = new_quiz
            question_copy.save()

            for choice in question.answer_set.all():
                choice_copy = deepcopy(choice)
                choice_copy.id = None
                choice_copy.question = question_copy
                choice_copy.save()

    def get_object(self):
        return Quiz.objects.get(id=self.kwargs['quiz_url'], is_active=True)

    def get_success_url(self) :
        return reverse_lazy('question_list', kwargs={'quiz_url' : self.request.session['quizid']})

    def post(self,request, *args, **kwargs) :
        self.object = self.get_object()
        self.quiz = self.object
        self.object.is_active = False
        self.object.save()
        self.object = deepcopy(self.object)
        return super(BaseUpdateView, self).post(request, *args, **kwargs) 

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.id = None
        self.object.is_active = True
        self.object.save()
        self.duplicate(self.quiz, self.object)
        self.request.session['quizid'] = self.object.id
        self.request.session['quizname'] = self.object.title
        if self.object.category :
            self.request.session['quizcategoryid'] = self.object.category.id
            self.request.session['quizcategory'] = self.object.category.category
        return HttpResponseRedirect(self.get_success_url())


class QuizList(ListView, LoginRequiredMixin) :
    model=Quiz
    template_name = 'indexTheme.html'

    def get_queryset(self):
        queryset = super(QuizList, self).get_queryset()
        friends = Friend.objects.friends(self.request.user).values_list('from_user', flat=True)
        return queryset.filter(Q(user__in=friends)|Q(user=self.request.user), Q(is_active=True)).order_by("-createdOn")

from el_pagination.decorators import page_template 

@page_template('indexPage.html')
def quizlist(request, template='indexTheme.html',extra_context=None):
    queryset = Quiz.objects.all()
    friends = Friend.objects.friends(request.user).values_list('from_user', flat=True)
    queryset = queryset.filter(Q(user__in=friends)|Q(user=request.user), Q(is_active=True)).order_by("-createdOn")
    context = {
        'entries': queryset,
    }
    if extra_context is not None:
        context.update(extra_context)
    return render_to_response(
        template, context, context_instance=RequestContext(request))


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super(UserCreateForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
        


class QuestionDelete(DeleteView, LoginRequiredMixin):
    model = Question

    def get_success_url(self) :
        return reverse_lazy('question_list', kwargs={'quiz_url' : self.kwargs['quiz_url']})

    def get(self, *args, **kwargs):
        return self.post(*args, **kwargs)


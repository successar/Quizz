from __future__ import unicode_literals
import re
import json

from django.db import models
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.validators import MaxValueValidator
from django.utils.translation import ugettext as _
from django.utils.timezone import now
from django.utils.encoding import python_2_unicode_compatible
from django.conf import settings

from model_utils.managers import InheritanceManager


class CategoryManager(models.Manager):

    def new_category(self, category):
        new_category = self.create(category=re.sub('\s+', '-', category)
                                   .lower())

        new_category.save()
        return new_category


@python_2_unicode_compatible
class Category(models.Model):

    category = models.CharField(verbose_name=_("Category"), max_length=250, blank=True, unique=True, null=True)

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.category


@python_2_unicode_compatible
class SubCategory(models.Model):

    sub_category = models.CharField(verbose_name=_("Sub-Category"), max_length=250, blank=True, null=True)

    category = models.ForeignKey(Category, null=True, blank=True, verbose_name=_("Category"))

    objects = CategoryManager()

    class Meta:
        verbose_name = _("Sub-Category")
        verbose_name_plural = _("Sub-Categories")

    def __str__(self):
        return self.sub_category + " (" + self.category.category + ")"


@python_2_unicode_compatible
class Quiz(models.Model):

    title = models.CharField(verbose_name=_("Title"), max_length=60, blank=False)

    description = models.TextField(verbose_name=_("Description"), blank=True, help_text=_("a description of the quiz"))

    url = models.SlugField(max_length=60, blank=False, help_text=_("a user friendly url"), verbose_name=_("user friendly url"))

    category = models.ForeignKey(Category, null=True, blank=True, verbose_name=_("Category"))

    random_order = models.BooleanField(blank=False, default=False, verbose_name=_("Random Order"), 
        help_text=_("Display the questions in a random order or as they are set?"))

    max_questions = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Max Questions"), 
        help_text=_("Number of questions to be answered on each attempt."))

    answers_at_end = models.BooleanField(blank=False, default=False, verbose_name=_("Answers at end"), 
        help_text=_("Correct answer is NOT shown after question. Answers displayed at the end."))

    exam_paper = models.BooleanField(blank=False, default=False, verbose_name=_("Exam Paper"), 
        help_text=_("If yes, the result of each attempt by a user will be stored. Necessary for marking."))

    single_attempt = models.BooleanField(blank=False, default=False, help_text=_("If yes, only one attempt by"
                    " a user will be permitted."
                    " Non users cannot sit this exam."), verbose_name=_("Single Attempt"))

    pass_mark = models.SmallIntegerField(blank=True, default=0, verbose_name=_("Pass Mark"), 
        help_text=_("Percentage required to pass exam."), validators=[MaxValueValidator(100)])

    success_text = models.TextField(blank=True, 
        help_text=_("Displayed if user passes."), verbose_name=_("Success Text"))

    fail_text = models.TextField(verbose_name=_("Fail Text"), blank=True, help_text=_("Displayed if user fails."))

    draft = models.BooleanField(blank=True, default=False, verbose_name=_("Draft"), 
        help_text=_("If yes, the quiz is not displayed"
                    " in the quiz list and can only be"
                    " taken by users who can edit"
                    " quizzes."))

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        self.url = re.sub('\s+', '-', self.url).lower()

        self.url = ''.join(letter for letter in self.url if
                           letter.isalnum() or letter == '-')

        if self.single_attempt is True:
            self.exam_paper = True

        if self.pass_mark > 100:
            raise ValidationError('%s is above 100' % self.pass_mark)

        super(Quiz, self).save(force_insert, force_update, *args, **kwargs)

    class Meta:
        verbose_name = _("Quiz")
        verbose_name_plural = _("Quizzes")

    def __str__(self):
        return self.title

    def get_questions(self):
        return self.question_set.all().select_subclasses()

    @property
    def get_max_score(self):
        return self.get_questions().count()


class ProgressManager(models.Manager):

    def new_progress(self, user):
        new_progress = self.create(user=user)
        new_progress.save()
        return new_progress


class Progress(models.Model):
    """
    Progress is used to track an individual signed in users score on different
    quiz's
    """
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name=_("User"))

    objects = ProgressManager()

    class Meta:
        verbose_name = _("User Progress")
        verbose_name_plural = _("User progress records")


    def show_exams(self):
        """
        Finds the previous quizzes marked as 'exam papers'.
        Returns a queryset of complete exams.
        """
        return Sitting.objects.filter(user=self.user, complete=True)


class SittingManager(models.Manager):

    def new_sitting(self, user, quiz):
        if quiz.random_order is True:
            question_set = quiz.question_set.all()
        else:
            question_set = quiz.question_set.all()

        question_set = question_set.values_list('id', flat=True)

        if len(question_set) == 0:
            raise ImproperlyConfigured('Question set of the quiz is empty. '
                                       'Please configure questions properly')

        if quiz.max_questions and quiz.max_questions < len(question_set):
            question_set = question_set[:quiz.max_questions]

        questions = ",".join(map(str, question_set)) + ","

        new_sitting = self.create(user=user, quiz=quiz, question_order=questions, question_list=questions, incorrect_questions="", current_score=0, complete=False, user_answers='{}')
        return new_sitting

    def user_sitting(self, user, quiz):
        if quiz.single_attempt is True and self.filter(user=user, quiz=quiz, complete=True)\
                                               .exists():
            return False

        try:
            sitting = self.get(user=user, quiz=quiz, complete=False)
        except Sitting.DoesNotExist:
            sitting = self.new_sitting(user, quiz)
        except Sitting.MultipleObjectsReturned:
            sitting = self.filter(user=user, quiz=quiz, complete=False)[0]
        return sitting


class Sitting(models.Model):
    """
    Used to store the progress of logged in users sitting a quiz.
    Replaces the session system used by anon users.

    Question_order is a list of integer pks of all the questions in the
    quiz, in order.

    Question_list is a list of integers which represent id's of
    the unanswered questions in csv format.

    Incorrect_questions is a list in the same format.

    Sitting deleted when quiz finished unless quiz.exam_paper is true.

    User_answers is a json object in which the question PK is stored
    with the answer the user gave.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_("User"))

    quiz = models.ForeignKey(Quiz, verbose_name=_("Quiz"))

    question_order = models.CommaSeparatedIntegerField(max_length=1024, verbose_name=_("Question Order"))

    question_list = models.CommaSeparatedIntegerField(max_length=1024, verbose_name=_("Question List"))

    incorrect_questions = models.CommaSeparatedIntegerField(max_length=1024, blank=True, verbose_name=_("Incorrect questions"))

    current_score = models.IntegerField(verbose_name=_("Current Score"))

    complete = models.BooleanField(default=False, blank=False, verbose_name=_("Complete"))

    user_answers = models.TextField(blank=True, default='{}', verbose_name=_("User Answers"))

    start = models.DateTimeField(auto_now_add=True, verbose_name=_("Start"))

    end = models.DateTimeField(null=True, blank=True, verbose_name=_("End"))

    objects = SittingManager()

    class Meta:
        permissions = (("view_sittings", _("Can see completed exams.")),)
        permissions = (("can_score", _("Can Change Score or mark correct/incorrect")),)

    def get_first_question(self):
        """
        Returns the next question.
        If no question is found, returns False
        Does NOT remove the question from the front of the list.
        """
        if not self.question_list:
            return False

        first, _ = self.question_list.split(',', 1)
        question_id = int(first)
        return Question.objects.get_subclass(id=question_id)

    def remove_first_question(self):
        if not self.question_list:
            return

        _, others = self.question_list.split(',', 1)
        self.question_list = others
        self.save()

    def add_to_score(self, points):
        self.current_score += int(points)
        self.save()

    @property
    def get_current_score(self):
        return self.current_score

    def _question_ids(self):
        return [int(n) for n in self.question_order.split(',') if n]

    @property
    def get_percent_correct(self):
        dividend = float(self.current_score)
        divisor = len(self._question_ids())
        if divisor < 1:
            return 0            # prevent divide by zero error

        if dividend > divisor:
            return 100

        correct = int(round((dividend / divisor) * 100))

        if correct >= 1:
            return correct
        else:
            return 0

    def mark_quiz_complete(self):
        self.complete = True
        self.end = now()
        self.save()

    def add_incorrect_question(self, question):
        """
        Adds uid of incorrect question to the list.
        The question object must be passed in.
        """
        if len(self.incorrect_questions) > 0:
            self.incorrect_questions += ','
        self.incorrect_questions += str(question.id) + ","
        if self.complete:
            self.add_to_score(-1)
        self.save()

    @property
    def get_incorrect_questions(self):
        """
        Returns a list of non empty integers, representing the pk of
        questions
        """
        return [int(q) for q in self.incorrect_questions.split(',') if q]

    def remove_incorrect_question(self, question):
        current = self.get_incorrect_questions
        current.remove(question.id)
        self.incorrect_questions = ','.join(map(str, current))
        self.add_to_score(1)
        self.save()

    @property
    def check_if_passed(self):
        return self.get_percent_correct >= self.quiz.pass_mark

    @property
    def result_message(self):
        if self.check_if_passed:
            return self.quiz.success_text
        else:
            return self.quiz.fail_text

    def add_user_answer(self, question, guess):
        current = json.loads(self.user_answers)
        current[question.id] = guess
        self.user_answers = json.dumps(current)
        self.save()

    def get_questions(self, with_answers=False):
        question_ids = self._question_ids()
        questions = sorted(self.quiz.question_set.filter(id__in=question_ids)
                                  .select_subclasses(), key=lambda q: question_ids.index(q.id))

        if with_answers:
            user_answers = json.loads(self.user_answers)
            for question in questions:
                question.user_answer = user_answers[str(question.id)]

        return questions

    @property
    def questions_with_user_answers(self):
        return {
            q: q.user_answer for q in self.get_questions(with_answers=True)
        }

    @property
    def get_max_score(self):
        return len(self._question_ids())

    def progress(self):
        """
        Returns the number of questions answered so far and the total number of
        questions.
        """
        answered = len(json.loads(self.user_answers))
        total = self.get_max_score
        return answered, total


@python_2_unicode_compatible
class Question(models.Model):
    """
    Base class for all question types.
    Shared properties placed here.
    """

    quiz = models.ManyToManyField(Quiz, verbose_name=_("Quiz"), blank=True)

    category = models.ForeignKey(Category, verbose_name=_("Category"), blank=True, null=True)

    sub_category = models.ForeignKey(SubCategory, verbose_name=_("Sub-Category"), blank=True, null=True)

    figure = models.ImageField(upload_to='uploads/%Y/%m/%d', blank=True, null=True, verbose_name=_("Figure"))

    content = models.CharField(max_length=1000, blank=False, help_text=_("Enter the question text that you want displayed"), verbose_name=_('Question'))

    explanation = models.TextField(max_length=2000, blank=True, help_text=_("Explanation to be shown after the question has been answered."), verbose_name=_('Explanation'))

    objects = InheritanceManager()

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['category']

    def __str__(self):
        return self.content

from django.conf.urls import url
from django.views.generic import TemplateView
from .views import CategoriesListView,\
    ViewQuizListByCategory, QuizUserProgressView,\
    QuizMarkingDetail, QuizTake, QuizCreate, QuestionCreate, QuizUpdate, QuestionList, QuestionUpdate, QuizList, quizlist, \
    QuestionDelete

urlpatterns = [        url(regex=r'^index$', 
                           view=quizlist,
                           name='index'),

                       url(regex=r'^category/$',
                           view=CategoriesListView.as_view(),
                           name='quiz_category_list_all'),

                       url(regex=r'^category/(?P<category_name>[\w|\W-]+)/$',
                           view=ViewQuizListByCategory.as_view(),
                           name='quiz_category_list_matching'),

                       url(regex=r'^$',
                           view=QuizUserProgressView.as_view(),
                           name='quiz_progress'),

                       url(regex=r'^marking/(?P<pk>[\d.]+)/$',
                           view=QuizMarkingDetail.as_view(),
                           name='quiz_marking_detail'),

                       url(regex=r'^new/$', 
                           view=QuizCreate.as_view(),
                           name='quiz_create'),

                       url(regex=r'^question/new/$', 
                           view=QuestionCreate.as_view(),
                           name='question_create'),

                       #  passes variable 'quiz_name' to quiz_take view
                       url(regex=r'^(?P<quiz_name>[\d.]+)/take/$',
                           view=QuizTake.as_view(),
                           name='quiz_question'),

                       url(regex=r'^question/new/$',
                           view = QuestionCreate.as_view(),
                           name='question_create'),

                       url(regex=r'^(?P<quiz_url>[\d.]+)/edit/$',
                           view = QuizUpdate.as_view(),
                           name='quiz_update'),

                       url(regex=r'^(?P<quiz_url>[\d.]+)/edit/questions/$',
                           view = QuestionList.as_view(),
                           name='question_list'),

                       url(regex=r'^(?P<quiz_url>[\d.]+)/edit/(?P<pk>[\w-]+)/$',
                           view = QuestionUpdate.as_view(),
                           name='question_update'),

                       url(regex=r'^(?P<quiz_url>[\d.]+)/delete/(?P<pk>[\w-]+)/$',
                           view = QuestionDelete.as_view(),
                           name='question_delete'),
]

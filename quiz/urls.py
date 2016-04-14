from django.conf.urls import url
from django.views.generic import TemplateView
from .views import CategoriesListView,\
    ViewQuizListByCategory, QuizUserProgressView,\
    QuizMarkingDetail, QuizTake, QuizCreate, QuestionCreate

urlpatterns = [        url(regex=r'^index$', 
                           view=TemplateView.as_view(template_name='IndexTheme.html'),
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

                       #  passes variable 'quiz_name' to quiz_take view
                       url(regex=r'^(?P<quiz_name>[\w-]+)/take/$',
                           view=QuizTake.as_view(),
                           name='quiz_question'),

                       url(regex=r'^question/new/$',
                           view = QuestionCreate.as_view(),
                           name='question_create'),
]

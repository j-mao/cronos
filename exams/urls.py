from django.urls import path

from . import views

app_name = "exams"

urlpatterns = [
    path(r"",
         views.course,
         name="course",
         ),
    path(r"<slug:quiz_identifier>/",
         views.quiz,
         name="quiz",
         ),
    path(r"<slug:quiz_identifier>/delete/",
         views.quiz_delete,
         name="quiz-delete",
         ),
    path(r"<slug:quiz_identifier>/edit/",
         views.quiz_edit,
         name="quiz-edit",
         ),
    path(r"<slug:quiz_identifier>/accommodations/",
         views.accommodation_summary,
         name="accommodation-summary",
         ),
    path(r"<slug:quiz_identifier>/request/<str:username>/",
         views.accommodation_request,
         name="accommodation-request",
         ),
]

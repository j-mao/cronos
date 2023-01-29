from django.urls import path

from . import views

app_name = "exams"

urlpatterns = [
    path(r"<int:year>/<str:season>/<str:course_number>/",
         views.course,
         name="course",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/<slug:quiz_identifier>/",
         views.quiz,
         name="quiz",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/<slug:quiz_identifier>/delete/",
         views.quiz_delete,
         name="quiz-delete",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/<slug:quiz_identifier>/edit/",
         views.quiz_edit,
         name="quiz-edit",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/<slug:quiz_identifier>/accommodations/",
         views.accommodation_summary,
         name="accommodation-summary",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/<slug:quiz_identifier>/request/<str:username>/",
         views.accommodation_request,
         name="accommodation-request",
         ),
]

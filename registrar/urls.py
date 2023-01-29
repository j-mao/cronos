from django.urls import path

from . import views

app_name = "registrar"

urlpatterns = [
    path(r"",
         views.index,
         name="index",
         ),
    path(r"<int:year>/<str:season>/",
         views.term,
         name="term",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/",
         views.course,
         name="course",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/edit/",
         views.course_edit,
         name="course-edit",
         ),
    path(r"<int:year>/<str:season>/<str:course_number>/delete/",
         views.course_delete,
         name="course-delete",
         ),
]

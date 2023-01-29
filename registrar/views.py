from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, reverse

from .forms import ClassJoinForm, CourseForm
from .models import Course, CourseListing, Term


def index(request):
    terms = Term.objects.filter(courses__isnull=False).distinct().order_by("-year", "-season")
    return render(request, "registrar/index.html", {"terms": terms})


def term(request, *, year, season):
    term = get_object_or_404(
        Term.objects.all(),
        year=year,
        season=season,
    )
    listings = CourseListing.objects.filter(course__term=term).order_by("number")

    form = None
    initial = {
        "year": year,
        "season": season,
    }
    if request.user.courses_taught.exists():
        if request.method == "POST":
            form = CourseForm(request.POST, user=request.user, initial=initial)
            if form.is_valid():
                instance = form.save()
                return HttpResponseRedirect(reverse("registrar:course", kwargs={"year": form.cleaned_data["year"], "season": form.cleaned_data["season"], "course_number": instance.listings.first().number}))
        else:
            form = CourseForm(user=request.user, initial=initial)
    return render(request, "registrar/term.html", {"form": form, "listings": listings})


def course(request, *, year, season, course_number):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    is_instructor = course.instructors.filter(pk=request.user.pk).exists()
    is_student = course.students.filter(pk=request.user.pk).exists()

    form = None

    if not is_instructor and not is_student:
        if request.method == "POST":
            form = ClassJoinForm(request.POST, course=course)
            if form.is_valid():
                course.students.add(request.user)
                return HttpResponseRedirect(reverse("registrar:course", kwargs={"year": year, "season": season, "course_number": course_number}))
        else:
            form = ClassJoinForm(course=course)

    return render(request, "registrar/course.html", {"form": form, "course": course, "is_instructor": is_instructor, "is_student": is_student})


def course_edit(request, *, year, season, course_number):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    if not course.instructors.filter(pk=request.user.pk).exists():
        raise PermissionDenied
    if request.method == "POST":
        form = CourseForm(request.POST, user=request.user, instance=course)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse("registrar:course", kwargs={"year": year, "season": season, "course_number": instance.listings.first().number}))
    else:
        form = CourseForm(user=request.user, instance=course)
    return render(request, "registrar/course_edit.html", {"form": form, "course": course})


def course_delete(request, *, year, season, course_number):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    if not course.instructors.filter(pk=request.user.pk).exists():
        raise PermissionDenied
    if request.method == "POST":
        course.delete()
        return HttpResponseRedirect(reverse("registrar:term", kwargs={"year": year, "season": season}))
    return render(request, "registrar/course_delete.html", {"course": course})

import os

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef, Prefetch
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.timezone import make_naive

from oidc.models import User
from registrar.models import Course

from .forms import (MessageCreateNewAccommodationForm,
                    MessageNoChangeAccommodationForm,
                    MessageRemoveAccommodationForm,
                    MessageUseExistingAccommodationForm, QuizForm)
from .models import Accommodation, AccommodationRequest, Message, Quiz


@login_required
def course(request, *, year, season, course_number):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    is_instructor = course.instructors.filter(pk=request.user.pk).exists()

    if is_instructor:
        if request.method == "POST":
            form = QuizForm(request.POST, course=course)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse("exams:course", kwargs={"year": year, "season": season, "course_number": course_number}))
        else:
            form = QuizForm(course=course)
    elif course.students.filter(pk=request.user.pk).exists():
        form = None
    else:
        raise PermissionDenied

    quizzes = Quiz.objects.filter(course=course).order_by("start").prefetch_related(
        Prefetch("accommodation_requests", queryset=AccommodationRequest.objects.filter(student=request.user), to_attr="my_accommodation_requests")
    )
    return render(request, "exams/course.html", {"form": form, "course": course, "quizzes": quizzes, "is_instructor": is_instructor})


@login_required
def quiz(request, *, year, season, course_number, quiz_identifier):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    quiz = get_object_or_404(
        Quiz.objects.all(),
        course=course,
        identifier=quiz_identifier,
    )
    if course.instructors.filter(pk=request.user.pk).exists():
        pass
    elif course.students.filter(pk=request.user.pk).exists():
        return HttpResponseRedirect(reverse("exams:accommodation-request", kwargs={"year": year, "season": season, "course_number": course_number, "quiz_identifier": quiz_identifier, "username": request.user.username}))
    else:
        raise PermissionDenied

    accommodations = Accommodation.objects.filter(quiz=quiz, accommodation_requests__isnull=False).distinct()
    accommodation_requests = AccommodationRequest.objects.filter(quiz=quiz).annotate(read=Exists(request.user.read_accommodation_requests.filter(pk=OuterRef("pk")))).order_by("read", "student__last_name", "student__first_name", "student__preferred_username")
    return render(request, "exams/quiz.html", {"quiz": quiz, "accommodations": accommodations, "accommodation_requests": accommodation_requests})


@login_required
def quiz_edit(request, *, year, season, course_number, quiz_identifier):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    quiz = get_object_or_404(
        Quiz.objects.all(),
        course=course,
        identifier=quiz_identifier,
    )
    if not course.instructors.filter(pk=request.user.pk).exists():
        raise PermissionDenied
    initial = {
        "start": make_naive(quiz.start),
        "end": make_naive(quiz.end),
    }
    if request.method == "POST":
        form = QuizForm(request.POST, course=course, instance=quiz, initial=initial)
        if form.is_valid():
            instance = form.save()
            return HttpResponseRedirect(reverse("exams:quiz", kwargs={"year": year, "season": season, "course_number": course_number, "quiz_identifier": instance.identifier}))
    else:
        form = QuizForm(course=course, instance=quiz, initial=initial)
    return render(request, "exams/quiz_edit.html", {"form": form, "quiz": quiz})


@login_required
def quiz_delete(request, *, year, season, course_number, quiz_identifier):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    quiz = get_object_or_404(
        Quiz.objects.all(),
        course=course,
        identifier=quiz_identifier,
    )
    if not course.instructors.filter(pk=request.user.pk).exists():
        raise PermissionDenied
    if request.method == "POST":
        quiz.delete()
        return HttpResponseRedirect(reverse("exams:course", kwargs={"year": year, "season": season, "course_number": course_number}))
    return render(request, "exams/quiz_delete.html", {"quiz": quiz})


@login_required
def accommodation_summary(request, *, year, season, course_number, quiz_identifier):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    quiz = get_object_or_404(
        Quiz.objects.all(),
        course=course,
        identifier=quiz_identifier,
    )
    if not course.instructors.filter(pk=request.user.pk).exists():
        raise PermissionDenied
    accommodation_requests = AccommodationRequest.objects.filter(quiz=quiz, accommodation__isnull=False).order_by("accommodation__location", "accommodation__start", "accommodation__end")
    return render(request, "exams/accommodations.html", {"quiz": quiz, "accommodation_requests": accommodation_requests})


@login_required
def accommodation_request(request, *, year, season, course_number, quiz_identifier, username):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    quiz = get_object_or_404(
        Quiz.objects.all(),
        course=course,
        identifier=quiz_identifier,
    )

    is_instructor = course.instructors.filter(pk=request.user.pk).exists()
    is_student = course.students.filter(pk=request.user.pk).exists()
    if is_student and username != request.user.username:
        raise PermissionDenied

    student = get_object_or_404(
        User.objects.all(),
        username=username,
    )
    accommodation_types = {
        "accommodation-no-change": {
            "display": "No action to accommodation",
            "form_cls": MessageNoChangeAccommodationForm,
        },
        "accommodation-remove": {
            "display": "Remove any assigned accommodations",
            "form_cls": MessageRemoveAccommodationForm,
        },
        "accommodation-use-existing": {
            "display": "Assign to existing accommodation",
            "form_cls": MessageUseExistingAccommodationForm,
        },
        "accommodation-create-new": {
            "display": "Create new accommodation",
            "form_cls": MessageCreateNewAccommodationForm,
        },
    }
    if is_instructor and request.GET.get("accommodation") not in accommodation_types:
        return HttpResponseRedirect(reverse("exams:accommodation-request", kwargs={"year": year, "season": season, "course_number": course_number, "quiz_identifier": quiz_identifier, "username": username}) + "?" + urlencode({"accommodation": "accommodation-no-change"}))

    if is_instructor:
        form_cls = accommodation_types[request.GET["accommodation"]]["form_cls"]
    elif is_student:
        form_cls = MessageNoChangeAccommodationForm
    else:
        raise PermissionDenied

    try:
        accommodation_request = AccommodationRequest.objects.get(quiz=quiz, student=student)
    except AccommodationRequest.DoesNotExist:
        accommodation = None
    else:
        accommodation_request.read_by.add(request.user)
        accommodation = accommodation_request.accommodation

    initial = {
        "start": make_naive(quiz.start),
        "end": make_naive(quiz.end),
    }
    if request.method == "POST":
        form = form_cls(request.POST, request.FILES, quiz=quiz, student=student, author=request.user, initial=initial)
        if form.is_valid():
            message = form.save()
            message.send_email_notifications(request=request)
            accommodation_request = message.request
            accommodation_request.read_by.remove(*accommodation_request.read_by.exclude(pk=request.user.pk).all())
            return HttpResponseRedirect(reverse("exams:accommodation-request", kwargs={"year": year, "season": season, "course_number": course_number, "quiz_identifier": quiz_identifier, "username": username}))
    else:
        form = form_cls(quiz=quiz, student=student, author=request.user, initial=initial)

    messages = Message.objects.filter(
        request__quiz=quiz,
        request__student=student,
    ).order_by("-created")

    return render(request, "exams/request.html", {"form": form, "quiz": quiz, "student": student, "accommodation": accommodation, "messages": messages, "is_instructor": is_instructor, "accommodation_types": accommodation_types})


@login_required
def attachment(request, *, year, season, course_number, quiz_identifier, username, message_id):
    course = get_object_or_404(
        Course.objects.all(),
        term__year=year,
        term__season=season,
        listings__number=course_number,
    )
    get_object_or_404(
        Quiz.objects.all(),
        course=course,
        identifier=quiz_identifier,
    )

    is_instructor = course.instructors.filter(pk=request.user.pk).exists()
    is_student = course.students.filter(pk=request.user.pk).exists()
    if is_student and username != request.user.username:
        raise PermissionDenied

    student = get_object_or_404(
        User.objects.all(),
        username=username,
    )
    message = get_object_or_404(
        Message.objects.all(),
        pk=message_id,
    )
    if not is_instructor and message.request.student != student:
        raise PermissionDenied
    if not message.attachment:
        return Http404

    fname = os.path.basename(message.attachment.name)
    with message.attachment.open("rb") as f:
        response = HttpResponse(f.read(), content_type="application/octet-stream", headers={
            "Content-Disposition": f'attachment; filename="{fname}"',
        })
        return response

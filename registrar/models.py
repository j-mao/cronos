import random
import string

from django.db import models
from django.utils.translation import gettext_lazy as _

from oidc.models import User


class TermSeason(models.TextChoices):
    Fall = "FA", _("Fall")
    WINTER = "JA", _("Winter")
    SPRING = "SP", _("Spring")
    SUMMER = "SU", _("Summer")


class Term(models.Model):
    year = models.PositiveIntegerField(help_text="The year of the term.")
    season = models.CharField(max_length=2, choices=TermSeason.choices, help_text="The season of the term.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["year", "season"], name="term-year-season-unique"),
        ]


def access_code_default():
    return "".join(random.choices(string.ascii_uppercase, k=6))


class Course(models.Model):
    name = models.CharField(max_length=128, help_text="The course name.")
    term = models.ForeignKey(Term, on_delete=models.PROTECT, help_text="The term.", related_name="courses")
    instructors = models.ManyToManyField(User, blank=True, related_name="courses_taught")
    students = models.ManyToManyField(User, blank=True, related_name="courses_taken")
    access_code = models.CharField(max_length=6, default=access_code_default, help_text="The joining access code.")


class CourseListing(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, help_text="The course.", related_name="listings")
    number = models.CharField(max_length=16, help_text="The number.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "number"], name="listing-course-number-unique"),
        ]

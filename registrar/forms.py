from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils.text import gettext_lazy as _

from .models import Course, CourseListing, Term, TermSeason, User


class ClassJoinForm(forms.Form):
    access_code = forms.CharField(label="Access code")

    def __init__(self, *args, course, **kwargs):
        super().__init__(*args, **kwargs)
        self._course = course
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    def clean_access_code(self):
        access_code = self.cleaned_data["access_code"].upper()
        if access_code != self._course.access_code:
            raise ValidationError(
                _("Incorrect access code"),
                code="incorrect_access_code",
            )
        return access_code


CourseListingFormSet = inlineformset_factory(Course, CourseListing, fields=("number",))


class CourseForm(forms.ModelForm):
    numbers = forms.CharField(max_length=128)
    year = forms.IntegerField(min_value=2000)
    season = forms.ChoiceField(choices=TermSeason.choices)
    instructor_usernames = forms.CharField()

    class Meta:
        model = Course
        fields = ["name", "numbers", "year", "season", "instructor_usernames"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self._user = user
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'
        if self.instance.pk is not None:
            self.fields["year"].disabled = True
            self.fields["year"].initial = self.instance.term.year
            self.fields["season"].disabled = True
            self.fields["season"].initial = self.instance.term.season
            self.fields["numbers"].initial = ", ".join(listing.number for listing in self.instance.listings.all())
            self.fields["instructor_usernames"].initial = ", ".join(instructor.preferred_username for instructor in self.instance.instructors.all())
        else:
            self.fields["instructor_usernames"].initial = user.preferred_username

    def clean_numbers(self):
        numbers = [number.strip() for number in self.cleaned_data["numbers"].split(",")]
        return numbers

    def clean_instructor_usernames(self):
        usernames = list({username.strip() for username in self.cleaned_data["instructor_usernames"].split(",")})
        for i, username in enumerate(usernames):
            try:
                user = User.objects.filter(preferred_username=username).order_by("-date_joined")[:1].get()
                usernames[i] = user.username
            except User.DoesNotExist:
                raise ValidationError(_("Unknown username."), code="unknown_username")
            else:
                usernames
        if self._user.username not in usernames:
            raise ValidationError(
                _("You cannot cause yourself to lose instructor status."),
                code="cannot_evict_self",
            )
        return usernames

    def clean(self, *args, **kwargs):
        cleaned = super().clean(*args, **kwargs)
        if CourseListing.objects.filter(course__term__year=cleaned["year"], course__term__season=cleaned["season"], number__in=cleaned["numbers"]).exclude(course=self.instance).exists():
            raise ValidationError(
                _("Course number already used."),
                code="number_in_use",
            )

    @transaction.atomic
    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        instance.term, created = Term.objects.get_or_create(
            year=self.cleaned_data["year"],
            season=self.cleaned_data["season"],
        )
        if commit:
            instance.save()
            self.save_m2m()

        instance.instructors.set(
            User.objects.filter(username__in=self.cleaned_data["instructor_usernames"])
        )

        CourseListing.objects.filter(course=instance).exclude(number__in=self.cleaned_data["numbers"]).delete()
        instance.listings.set([
            CourseListing.objects.get_or_create(course=instance, number=number)[0]
            for number in self.cleaned_data["numbers"]
        ])
        return instance

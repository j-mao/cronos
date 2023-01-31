import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.utils.text import gettext_lazy as _
from django.utils.text import slugify
from django.utils.timezone import make_aware

from registrar.models import User

from .models import Accommodation, AccommodationRequest, Message, Quiz


class QuizForm(forms.ModelForm):
    start = forms.CharField(widget=forms.TextInput(attrs={"type": "datetime-local"}))
    end = forms.CharField(widget=forms.TextInput(attrs={"type": "datetime-local"}))

    class Meta:
        model = Quiz
        fields = ["name", "start", "end"]

    def __init__(self, *args, course, **kwargs):
        super().__init__(*args, **kwargs)
        self._course = course
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    def clean(self, *args, **kwargs):
        if Quiz.objects.filter(course=self._course, identifier=slugify(self.cleaned_data["name"])).exclude(pk=self.instance.pk).exists():
            raise ValidationError(
                _("Quiz name is too similar to another quiz"),
                code="quiz_name_too_similar",
            )

    def clean_start(self):
        return make_aware(datetime.datetime.fromisoformat(self.cleaned_data["start"]))

    def clean_end(self):
        return make_aware(datetime.datetime.fromisoformat(self.cleaned_data["end"]))

    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        instance.identifier = slugify(instance.name)
        instance.course = self._course
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class AbstractMessageForm(forms.ModelForm):
    update_accommodation = forms.BooleanField(required=False)

    class Meta:
        model = Message
        fields = ["body", "attachment", "update_accommodation"]

    def __init__(self, *args, quiz: Quiz, student: User, author: User, **kwargs):
        super().__init__(*args, **kwargs)
        self._quiz = quiz
        self._student = student
        self._author = author
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        instance.request, created = AccommodationRequest.objects.get_or_create(quiz=self._quiz, student=self._student)
        instance.author = self._author

        if commit:
            instance.save()
            self.save_m2m()
        return instance


class MessageNoChangeAccommodationForm(AbstractMessageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["body"].required = True

    def clean_update_accommodation(self):
        return False


class MessageRemoveAccommodationForm(AbstractMessageForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_update_accommodation(self):
        return True


class MessageUseExistingAccommodationForm(AbstractMessageForm):
    class Meta(AbstractMessageForm.Meta):
        fields = ["body", "attachment", "update_accommodation", "accommodation"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["accommodation"].queryset = Accommodation.objects.filter(
            quiz=self._quiz,
            accommodation_requests__isnull=False
        ).distinct()
        self.fields["accommodation"].required = True

    def clean_update_accommodation(self):
        return True


class MessageCreateNewAccommodationForm(AbstractMessageForm):
    location = forms.CharField(max_length=16)
    start = forms.CharField(widget=forms.TextInput(attrs={"type": "datetime-local"}))
    end = forms.CharField(widget=forms.TextInput(attrs={"type": "datetime-local"}))
    comments = forms.CharField(max_length=1024, required=False)

    class Meta(AbstractMessageForm.Meta):
        fields = ["body", "attachment", "update_accommodation", "location", "start", "end", "comments"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_update_accommodation(self):
        return True

    def clean_start(self):
        return make_aware(datetime.datetime.fromisoformat(self.cleaned_data["start"]))

    def clean_end(self):
        return make_aware(datetime.datetime.fromisoformat(self.cleaned_data["end"]))

    def save(self, commit: bool = True):
        instance = super().save(commit=False)
        instance.accommodation = Accommodation.objects.create(
            quiz=self._quiz,
            location=self.cleaned_data["location"],
            start=self.cleaned_data["start"],
            end=self.cleaned_data["end"],
            comments=self.cleaned_data["comments"],
        )
        if commit:
            instance.save()
            self.save_m2m()
        return instance

import os
import uuid

from django.core.mail import send_mail
from django.db import models, transaction
from django.template import engines

from registrar.models import Course, User


class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, help_text="The course of the quiz.", related_name="quizzes")
    identifier = models.SlugField(max_length=128, help_text="A unique identifying code for the quiz.")
    name = models.CharField(max_length=128, help_text="The name of the quiz.")
    start = models.DateTimeField(help_text="The scheduled quiz start time.")
    end = models.DateTimeField(help_text="The scheduled quiz end time.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", "identifier"], name="quiz-course-identifier-unique"),
        ]


class Accommodation(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, help_text="The quiz being accommodated.", related_name="accommodations")
    location = models.CharField(max_length=16, help_text="The location of the accommodation.")
    start = models.DateTimeField(help_text="The scheduled accommodation start time.")
    end = models.DateTimeField(help_text="The scheduled accommodation end time.")
    comments = models.CharField(max_length=1024, help_text="Any specific details of the accommodation.")

    def __str__(self):
        template = engines["django"].from_string("{{ location }} from {{ start }} to {{ end }}; {{ comments }}")
        return template.render(context=self.__dict__)


class AccommodationRequest(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, help_text="The quiz being requested for accommodation.", related_name="accommodation_requests")
    student = models.ForeignKey(User, on_delete=models.CASCADE, help_text="The student requesting the accommodation.", related_name="accommodation_requests")
    accommodation = models.ForeignKey(Accommodation, on_delete=models.RESTRICT, null=True, blank=True, help_text="The assigned accommodation.", related_name="accommodation_requests")
    read_by = models.ManyToManyField(User, blank=True, help_text="Who has read the latest messages in this request.", related_name="read_accommodation_requests")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["quiz", "student"], name="accommodation_request-quiz-student-unique"),
        ]


def message_attachment_path(instance, filename):
    return os.path.join(instance.author.username, str(uuid.uuid4()), filename)


class Message(models.Model):
    request = models.ForeignKey(AccommodationRequest, on_delete=models.CASCADE, help_text="The request this message is for.", related_name="messages")
    created = models.DateTimeField(auto_now_add=True, help_text="When this message was posted.")
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, help_text="The message author.", related_name="messages")
    body = models.TextField(max_length=10000, blank=True, help_text="The message content.")
    attachment = models.FileField(null=True, blank=True, upload_to=message_attachment_path, help_text="Any file attachments to the message.")
    accommodation = models.ForeignKey(Accommodation, on_delete=models.RESTRICT, null=True, blank=True, help_text="The accommodation assigned as part of this message.", related_name="messages")
    update_accommodation = models.BooleanField(help_text="Whether this message updated the accommodation.")

    @transaction.atomic
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update accommodation request with latest outcome
        try:
            latest = Message.objects.filter(request=self.request, update_accommodation=True).order_by("-created")[:1].get()
        except Message.DoesNotExist:
            pass
        else:
            if self.request.accommodation != latest.accommodation:
                self.request.accommodation = latest.accommodation
                self.request.save(update_fields=["accommodation"])
        # Send mail to notify of update
        recipients = (
            list(self.request.quiz.course.instructors.all())
            if self.author == self.request.student
            else [self.request.student]
        )
        send_mail(
            subject=f"[cronos] Accommodation request for {self.request.quiz.name}",
            message=f"""
Hello! There was an update to the accommodation request by {self.request.student.username} for {self.request.quiz.name}.
Please visit Cronos to view the message.

Do not reply to this email.
            """,
            from_email=None,
            recipient_list=[recipient.email for recipient in recipients],
        )

    def attachment_filename(self):
        return os.path.basename(self.attachment.name)

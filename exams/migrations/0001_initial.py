# Generated by Django 4.1.5 on 2023-02-07 20:22

from django.db import migrations, models
import exams.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Accommodation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('location', models.CharField(help_text='The location of the accommodation.', max_length=16)),
                ('start', models.DateTimeField(help_text='The scheduled accommodation start time.')),
                ('end', models.DateTimeField(help_text='The scheduled accommodation end time.')),
                ('comments', models.CharField(help_text='Any specific details of the accommodation.', max_length=1024)),
            ],
        ),
        migrations.CreateModel(
            name='AccommodationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, help_text='When this message was posted.')),
                ('body', models.TextField(blank=True, help_text='The message content.', max_length=10000)),
                ('attachment', models.FileField(blank=True, help_text='Any file attachments to the message.', null=True, upload_to=exams.models.message_attachment_path)),
                ('update_accommodation', models.BooleanField(help_text='Whether this message updated the accommodation.')),
            ],
        ),
        migrations.CreateModel(
            name='Quiz',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('identifier', models.SlugField(help_text='A unique identifying code for the quiz.', max_length=128)),
                ('name', models.CharField(help_text='The name of the quiz.', max_length=128)),
                ('start', models.DateTimeField(help_text='The scheduled quiz start time.')),
                ('end', models.DateTimeField(help_text='The scheduled quiz end time.')),
            ],
        ),
    ]

from django.contrib import admin

from .models import Course, CourseListing, Term


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    pass


class CourseListingInline(admin.TabularInline):
    model = CourseListing


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseListingInline]
